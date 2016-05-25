import pickle
from io import BytesIO
from collections import OrderedDict, Mapping

from astropy.io import fits

from .abstract_base_traits import *
from ..exceptions import DataNotAvailable
from .utilities import TraitProperty, TraitMapping, TraitKey

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

    _sub_traits = TraitMapping()

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


        schema = dict()
        for trait_property in cls._trait_properties():
                schema[trait_property.name] = trait_property.type

        if include_subtraits:
            for trait_type in cls._sub_traits.get_trait_types():
                # Create empty this sub-trait type:
                schema[trait_type] = dict()
                # Populate the dict with schema from each sub-type:
                for trait_class in cls.sub_traits(trait_type_filter=trait_type):
                    # FIXME: This will break if different sub-traits have different schemas (I think).
                    #
                    #   The update needs to be done recursively, not just on the top
                    #   level of the sub-trait dictionary. Otherwise, the schema
                    #   produced will be incomplete. This can best be fixed by
                    #   implementing a special sub-class of dict expressly for this
                    #   purpose, which knows how to do such a recurisve update.
                    schema[trait_type].update(trait_class.schema())

        return schema

    @classmethod
    def sub_traits(cls, trait_type_filter=None):
        """Generate list of sub_traits.

        :parameter trait_type_filter:
            The list of trait_types that should be included in the results, or None for all Traits.

        :returns:
            The sub-trait classes (not instances!).

        """

        if trait_type_filter is None:
            # Include all sub-traits
            trait_type_filter = cls._sub_traits.get_trait_types()

        for trait_class in cls._sub_traits.get_traits_for_type(trait_type_filter):
            yield trait_class

    def __init__(self, archive, trait_key=None, object_id=None, parent_trait=None, loading='lazy'):
        super().__init__()
        self.archive = archive
        self.trait_key = trait_key
        self.version = trait_key.version
        self.object_id = object_id
        self._parent_trait = parent_trait
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

    def get_sub_trait(self, trait_key):

        if trait_key is None:
            raise ValueError("The TraitKey must be provided.")
        if not isinstance(trait_key, TraitKey) and isinstance(trait_key, tuple):
            trait_key = TraitKey(*trait_key)

        # Check if we have already loaded this trait, otherwise load and cache it here.
        if trait_key not in self._trait_cache:

            # Check the size of the cache, and remove item if necessary
            # This should probably be more clever.
            while len(self._trait_cache) > 20:
                self._trait_cache.popitem(last=False)

            # Determine which class responds to the requested trait.
            # Potential for far more complex logic here in future.
            trait_class = self._sub_traits[trait_key]

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


