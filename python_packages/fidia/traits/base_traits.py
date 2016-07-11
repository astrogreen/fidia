import pickle
from io import BytesIO
from collections import OrderedDict, Mapping

from contextlib import contextmanager

from astropy.io import fits

import astropy.coordinates
import astropy.wcs

from .abstract_base_traits import *
from ..exceptions import DataNotAvailable
from .utilities import TraitProperty, TraitKey, TRAIT_NAME_RE
from .trait_registry import TraitRegistry
from ..utilities import SchemaDictionary
from ..descriptions import PrettyName, Description, Documentation

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()


# class DictTrait(Mapping):
#     """A "mix-in class which provides dict-like access for Traits
#
#     Requires that the class mixed into implements a `_trait_dict` cache
#
#     """
#
#     def __iter__(self):
#         pass
#     def __getitem__(self, item):
#         if item in self._trait_cache:
#             return self._trait_cache[item]
#         else:
#             return getattr(self, item)
#
#     def __len__(self):
#         return 0

class Trait(AbstractBaseTrait):

    sub_traits = TraitRegistry()


    pretty_name = PrettyName()
    description = Description()
    documentation = Documentation()

    # The following are a required part of the Trait interface.
    # They must be set in sub-classes to avoid an error trying create a Trait.
    trait_type = None
    qualifiers = None
    available_versions = None


    @classmethod
    def schema(cls, include_subtraits=True):
        """Provide the schema of data in this trait as a dictionary.

        The schema is presented as a dictionary, where the keys are strings
        giving the name of the attributes defined, and the values are the FIDIA
        type strings for each attribute.

        Only attributes which are TraitProperties are included in the schema.

        Examples:

            >>> galaxy['redshift'].schema()
            {'value': 'float', 'variance': 'float'}

        """


        schema = SchemaDictionary()
        for trait_property in cls._trait_properties():
                schema[trait_property.name] = trait_property.type

        if include_subtraits:
            for trait_type in cls.sub_traits.get_trait_names():
                # Create empty this sub-trait type:
                schema[trait_type] = SchemaDictionary()
                # Populate the dict with schema from each sub-type:
                for trait_class in cls.sub_traits.get_traits(trait_type_filter=trait_type):
                    schema[trait_type].update(trait_class.schema())

        return schema

    # @classmethod
    # def sub_traits(cls, trait_type_filter=None):
    #     """Generate list of sub_traits.
    #
    #     :parameter trait_type_filter:
    #         The list of trait_types that should be included in the results, or None for all Traits.
    #
    #     :returns:
    #         The sub-trait classes (not instances!).
    #
    #     """
    #
    #     if trait_type_filter is None:
    #         # Include all sub-traits
    #         trait_type_filter = cls._sub_traits.get_trait_names()
    #
    #     for trait_class in cls._sub_traits.get_traits_for_type(trait_type_filter):
    #         yield trait_class

    @classmethod
    def answers_to_trait_name(cls, trait_name):
        match = TRAIT_NAME_RE.fullmatch(trait_name)
        if match is not None:
            log.debug("TraitName match results: %s", match.groupdict())
            # Confirm that the qualifier has been used correctly:
            if match.group('trait_qualifier') is not None and cls.qualifiers is None:
                raise ValueError("Trait type '%s' does not allow a qualifier.")
            if match.group('trait_qualifier') is None and cls.qualifiers is not None:
                raise ValueError("Trait type '%s' does requires a qualifier.")

            # Check the trait name against all possible trait_names supported by this Trait.
            if match.group('trait_type') != cls.trait_type:
                return False
            if cls.qualifiers is not None \
                    and match.group('trait_qualifier') not in cls.qualifiers:
                return False
            return True
        else:
            return False

    @classmethod
    def _validate_trait_class(cls):
        assert cls.trait_type is not None
        # assert cls.available_versions is not None

    def __init__(self, archive, trait_key=None, object_id=None, parent_trait=None, loading='lazy'):
        super().__init__()

        self._validate_trait_class()

        self.archive = archive
        assert isinstance(trait_key, TraitKey), "In creation of Trait, trait_key must be a TraitKey, got %s" % trait_key
        self.trait_key = trait_key
        if trait_key.branch is None and parent_trait is not None:
            # Inherit branch from parent trait:
            self.branch = parent_trait.branch
        else:
            self.branch = trait_key.branch

        # Trait Version handling:
        #
        #   The goal of this is to set the trait version if at all possible. The
        #   following are tried:
        #   - If version explicitly provided in this initialisation, that is the version.
        #   - If this is a sub trait, check the parent trait for it's version.
        #   - If the version is still none, try to set it to the default for this trait.
        #
        if trait_key.version is None and parent_trait is not None:
            # Inherit version from parent trait, if permitted
            if self.available_versions is not None and parent_trait.version in self.available_versions:
                self.version = parent_trait.version
            else:
                self.version = None
        else:
            self.version = trait_key.version
        # if self.version is None:
        #     self.version = self.default_version

        if object_id is None:
            raise KeyError("object_id must be supplied")
        self.object_id = object_id
        self.parent_trait = parent_trait
        self.trait_qualifier = trait_key.trait_qualifier

        self._trait_cache = OrderedDict()

        if parent_trait is not None:
            self.trait_path = parent_trait.trait_path + tuple(self.trait_key)
        else:
            self.trait_path = tuple(self.trait_key)


        # The preload count is used to track how many accesses there are to this
        # trait so that it can be properly cleaned up when all loads are
        # complete.
        self._preload_count = 0

        if loading not in ('eager', 'lazy', 'verylazy'):
            raise ValueError("loading keyword must be one of ('eager', 'lazy', 'verylazy')")
        self._loading = loading

        # Call user provided `init` funciton
        self.init()

        # Preload all traits
        # @TODO: Modify preloading to respect preload argument
        self._trait_dict = dict()
        if self._loading == 'eager':
            self._realise()

    @property
    def trait_name(self):
        return self.trait_key.trait_name

    def get_sub_trait(self, trait_key):
        """Retrieve a subtrait for the TraitKey.

        trait_key can be a TraitKey, or anything that can be interpreted as a TraitKey
        (using `TraitKey.as_traitkey`)

        """
        if trait_key is None:
            raise ValueError("The TraitKey must be provided.")
        if not isinstance(trait_key, TraitKey):
            trait_key = TraitKey.as_traitkey(trait_key)

        # Check if we have already loaded this trait, otherwise load and cache it here.
        if trait_key not in self._trait_cache:

            # Check the size of the cache, and remove item if necessary
            # This should probably be more clever.
            while len(self._trait_cache) > 20:
                self._trait_cache.popitem(last=False)

            # Determine which class responds to the requested trait.
            # Potential for far more complex logic here in future.
            trait_class = self.sub_traits.retrieve_with_key(trait_key)

            # Create the trait object and cache it
            log.debug("Returning trait_class %s", type(trait_class))
            trait = trait_class(self.archive, trait_key, parent_trait=self, object_id=self.object_id)

            self._trait_cache[trait_key] = trait

        return self._trait_cache[trait_key]

    # @property
    # def trait_name(self):
    #     return self.trait_qualifier


    def init(self):
        """Extra initialisations for a Trait.

        Override this function with any extra initialisation required for this
        trait, but not things such as opening files or connecting to a database:
        see `preload` and `cleanup` for those things.

        """
        pass

    def preload(self):
        """Prepare for a trait property to be retrieved using plugin code.

        Override this function with any initialisation required for this trait
        to load its data, such as opening required files, connecting to databases, etc.

        """
        pass

    def cleanup(self):
        """Cleanup after a trait property has been retrieved using plugin code.

        Override this function with any cleanup that should be done once this trait
        to loaded its data, such as closing files.

        """
        pass

    @classmethod
    def _trait_properties(cls, trait_property_types=None):
        """Generator which iterates over the TraitProperties attached to this Trait.

        :param trait_property_types:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        Note that the descriptor must be handed this Trait object to actually retrieve
        data, which is why this is implemented as a private method. See
        `trait_property_values` as a simpler alternative.

        Alternately, use the public `trait_properties` method to retrieve bound
        Trait Properties which do not have this complication (and see ASVO-425!)

        :returns: the TraitProperty descriptor object

        """

        if isinstance(trait_property_types, str):
            trait_property_types = tuple(trait_property_types)

        # Search class attributes:
        log.debug("Searching for TraitProperties of Trait '%s' with type in %s", cls.trait_type, trait_property_types)
        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, TraitProperty):
                log.debug("Found trait property '{}' of type '{}'".format(attr, obj.type))
                if (trait_property_types is None) or (obj.type in trait_property_types):
                    yield obj

    # def sub_traits(self):
    #     """Generator which iterates over the sub-Traits of this Trait."""
    #
    #     for key in dir(type(self)):
    #         obj = getattr(type(self), key)
    #         if isinstance(obj, TraitProperty):
    #             log.debug("Found trait property '{}'".format(key))
    #             yield obj

    @classmethod
    def trait_property_dir(cls):
        """Return a directory of TraitProperties for this object, similar to what the builtin `dir()` does."""
        for tp in cls._trait_properties():
            yield tp.name

    def trait_properties(self, trait_property_types=None):
        """Generator which iterates over the (Bound)TraitProperties attached to this Trait.

        :param trait_property_types:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        :yields: a TraitProperty which is bound to this trait

        """

        # If necessary, convert a single trait property type argument to a list:
        if isinstance(trait_property_types, str):
            trait_property_types = tuple(trait_property_types)

        # Search class attributes. NOTE that this code is very similar to that
        # in `_trait_properties`. It has been reproduced here as
        # `_trait_properties` is probably going to be deprecated and removed if
        # ASVO-425 works out.
        #
        # Also note that, as written, this method avoids creating
        # BoundTraitProperty objects unless actually necessary.
        log.debug("Searching for TraitProperties of Trait '%s' with type in %s", self.trait_type, trait_property_types)
        cls = type(self)
        for attr in dir(cls):
            descriptor_obj = getattr(cls, attr)
            if isinstance(descriptor_obj, TraitProperty):
                log.debug("Found trait property '{}' of type '{}'".format(attr, descriptor_obj.type))
                if (trait_property_types is None) or (descriptor_obj.type in trait_property_types):
                    # Retrieve the attribute for this object (which will create
                    # the BoundTraitProperty: see `__get__` on `TraitProperty`)
                    yield getattr(self, attr)

    # def sub_traits(self):
    #     """Generator which iterates over the sub-Traits of this Trait."""
    #
    #     for key in dir(type(self)):
    #         obj = getattr(type(self), key)
    #         if isinstance(obj, TraitProperty):
    #             log.debug("Found trait property '{}'".format(key))
    #             yield obj

    def trait_property_values(self, trait_type=None):
        """Generator which returns the values of the TraitProperties of the given type.


        :return: the value of each TraitProperty (not the descriptor object)

        """
        for tp in self._trait_properties(trait_type):
            yield getattr(self, tp.name).value

    @contextmanager
    def preloaded_context(self):
        """Returns a context manager reference to the preloaded trait, and cleans up afterwards."""
        try:
            # Preload the Trait if necessary.
            self._load_incr()
            log.debug("Context manager version of Trait %s created", self.trait_key)
            yield self
        finally:
            # Cleanup the Trait if necessary.
            self._load_decr()
            log.debug("Context manager version of Trait %s cleaned up", self.trait_key)

    def _load_incr(self):
        """Internal function to handle preloading. Prevents a Trait being loaded multiple times.

        This function should be called prior to anything which requires calling
        TraitProperty loaders, typically only by the TraitProperty object
        itself.
        """
        assert self._preload_count >= 0
        if self._preload_count == 0:
            self.preload()
        self._preload_count += 1

    def _load_decr(self):
        """Internal function to handle cleanup.

        This function should be called after anything which requires calling
        TraitProperty loaders, typically only by the TraitProperty object
        itself.
        """
        assert self._preload_count > 0
        if self._preload_count == 1:
            self.cleanup()
        self._preload_count -= 1

    def _realise(self):
        """Search through the objects members for TraitProperties, and preload any found.


        """

        log.debug("Realising...")

        # Check and if necessary preload the trait.
        self._load_incr()

        # Iterate over the trait properties, loading any not already in the
        # `_trait_dict` cache
        for traitprop in self._trait_properties():
            if traitprop.name not in self._trait_dict:
                self._trait_dict[traitprop.name] = traitprop.fload(self)

        # Check and if necessary cleanup the trait.
        self._load_decr()

    def as_bytes(self):
        """Return a representation of this TraitProperty as a serialized string of bytes"""
        dict_to_serialize = self._trait_dict
        with BytesIO() as byte_file:
            pickle.dump(dict_to_serialize, byte_file)
            return byte_file.getvalue()

    def as_fits(self, file):
        """FITS Exporter

        :param  file
            file is either a file-like object, or a string containing the path
            of a file to be created. In the case of the string, the file will be
            created, written to, and closed.

        :returns None

        """


        # Create a function holder which can be set to close the file if it is opened here
        file_cleanup = lambda: None
        if isinstance(file, str):
            file = open(file, 'wb')
            # Store pointer to close function to be called at the end of the this function.
            file_cleanup = file.close

        hdulist = fits.HDUList()

        # Value should/will always be the first item in the FITS File (unless it cannot
        # be put in a PrimaryHDU, e.g. because it is not "image-like")

        if type(self).value.type in ("float.array", "int.array"):
            primary_hdu = fits.PrimaryHDU(self.value())
            hdulist.append(primary_hdu)
        elif type(self).value.type in ("float", "int"):
            primary_hdu = fits.PrimaryHDU([self.value()])
            hdulist.append(primary_hdu)
        else:
            log.error("Attempted to export trait with value type '%s'", type(self).value.type)
            raise NotImplementedError("Cannot export this trait as FITS")

        # Attach all "meta-data" Traits to Header of Primary HDU
        # for trait in self.sub_traits(MetaDataTrait):
        #     primary_hdu.header[trait.short_name] = (trait.value, trait.short_comment)

        # Attach all simple value Traits to header of Primary HDU:
        # for trait in self.get_sub_trait(Measurement):
        #     primary_hdu.header[trait.short_name] = (trait.value, trait.short_comment)
        #     primary_hdu.header[trait.short_name + "_ERR"] = (trait.value, trait.short_comment)

        # Create extensions for additional array-like values
        for trait_property in self.trait_properties(['float.array', 'int.array']):
            extension = fits.ImageHDU(trait_property.value)
            extension.name = trait_property.name
            hdulist.append(extension)

        # Add single-value TraitProperties to the header:
        for trait_property in self._trait_properties(['float', 'int']):
            primary_hdu.header[trait_property.name] = (
                getattr(self, trait_property.name),
                trait_property.doc)

        for trait_property in self._trait_properties(['string']):
            value = getattr(self, trait_property.name)
            if len(value) >= 80:
                continue
            primary_hdu.header[trait_property.name] = (
                value,
                trait_property.doc)

        # Create extensions for additional record-array-like values (e.g. tabular values)
        # for trait_property in self.trait_property_values('catalog'):
        #     extension = fits.BinTableHDU(trait_property)
        #     hdulist.append(extension)

        hdulist.verify('exception')
        hdulist.writeto(file)

        # If necessary, close the open file handle.
        file_cleanup()

    def __getitem__(self, key):
        """Provide dictionary-like retrieve of sub-traits"""
        return self.get_sub_trait(key)

class Measurement(Trait, AbstractMeasurement): pass

class Velocity(Measurement): pass

class Map(Trait, AbstractBaseArrayTrait):
    """Maps provide "relative spatial information", i.e. they add spatial
    information to existing data, such as a set of spectra or classifications.
    For relative spatial information to be meaningful, there must be at least
    two pieces of information. Therefore, we define map as a list of other
    objects which also have spatial information.

    """


    # A list of positions
    @property
    def spatial_information(self):
        return self._spatial_information
    
    # The centre, starting point, or other canonical position information
    @property
    def nominal_position(self):
        return self._nominal_position
    

class MetadataTrait(Trait):
    def __init__(self, *args, **kwargs):
        super(MetadataTrait, self).__init__(*args, **kwargs)




class DetectorCharacteristics(MetadataTrait):
    """

    Trait Properties:

        detector_id

        detector_size

        gain

        read_noise


    """

    required_trait_properties = {
        'detector_id': 'string',
        'detector_size': 'string',
        'gain': 'float',
        'read_noise': 'float'
    }

class SpectrographCharacteristics(Trait):
    """

    Trait Properties:

        instrument_name

        arm

        disperser_id

        disperser_configuration

        control_software

    """

    pass

class OpticalTelescopeCharacteristics(Trait):
    """

    Trait Properties:

        observatory_name

        latitude

        longitude

        altitude

        focus_configuration



    """
    pass


class SmartTrait(Trait):
    pass

class SkyCoordinate(astropy.coordinates.SkyCoord, SmartTrait):

    trait_type = 'sky_coordinate'

    def __init__(self, *args, **kwargs):
        SmartTrait.__init__(self, *args, **kwargs)
        astropy.coordinates.SkyCoord.__init__(self, self._ra(), self._dec(), unit='deg', frame=self._ref_frame)

    # @FIXME: explain why value is required here but not for WorldCoordinateSystem below.
    @property
    def value(self):
        return None

    @abstractproperty
    def _ra(self):
        return NotImplementedError

    @abstractproperty
    def _dec(self):
        return NotImplementedError

    @property
    def _ref_frame(self):
        return 'icrs'


class WorldCoordinateSystem(astropy.wcs.WCS, SmartTrait):

    # This could be implemented in one of two ways (I think):
    #
    # Way 1:
    #
    #     Override `__new__` and use it to return an object which is not of the
    #     type of this class, i.e. a WCS object instead of this Trait. In a
    #     similar vein, __new__ could be used to fiddle with the initialisation
    #     order as I suggest below in Way 2.
    #
    # Way 2
    #
    #     Override `__init__`, and instead of calling super().__init__(), call the
    #     superclass initialisations explicitly and separately, making it
    #     possible to get the Trait part of the object set up first, and then
    #     use that setup to initialize the WCS object.

    # The second method is probably fairly easy to implement:
    #     def __init__(self, *args, **kwargs):
    #         SmartTrait.__init__(self, *args, **kwargs)
    #         astropy.wcs.WCS.__init__(self, header=self._wcs_string)
    #
    # However, there are a few issues with this approach... (???)

    trait_type = 'wcs'

    def __init__(self, *args, **kwargs):
        SmartTrait.__init__(self, *args, **kwargs)
        header_string = self._wcs_string.value
        log.debug("Initialising WCS object with %s containing %s", type(header_string), header_string)
        astropy.wcs.WCS.__init__(self, header=header_string)

    @abstractproperty
    def _wcs_string(self):
        return NotImplementedError

    def as_fits(self, file):
        # Not possible to create a FITS file for a WCS trait.
        # TODO: See if this method can be hidden or deleted.
        # TODO: Perhaps handle this by moving as_fits() off of the top level Trait class.
        return None

class Spectrum(Measurement, AbstractBaseArrayTrait): pass

class Epoch(Measurement):

    @property
    def epoch(self):
        return self


class TimeSeries(Epoch, AbstractBaseArrayTrait): pass


class Image(Map): pass


class SpectralMap(Trait, AbstractBaseArrayTrait):
    """

    Required trait_properties:

        value
        variance
        covariance
        weight

    """

    @abstractproperty
    def value(self): pass

    @abstractproperty
    def variance(self): pass

    # @abstractproperty
    # def covariance(self): pass
    #
    # @abstractproperty
    # def weight(self): pass

class Classification(Trait, AbstractBaseClassification): pass


