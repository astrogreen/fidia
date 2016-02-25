import pickle
from io import BytesIO
from collections import OrderedDict

from astropy.io import fits

from .abstract_base_traits import *
from ..exceptions import DataNotAvailable
from .utilities import TraitProperty, TraitMapping, TraitKey

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()




class Trait(AbstractBaseTrait):

    @classmethod
    def schema(cls):
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
        for attr in dir(cls):
            if isinstance(getattr(cls, attr), TraitProperty):
                schema[attr] = getattr(cls, attr).type

        return schema

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

    def sub_traits(self, trait_type_filter=None):
        """(NOT IMPLEMENTED) Generate list of sub_traits.

        :parameter trait_type_filter:
            The list of Trait Classes that should be included in the results, or None for all Traits.

        :returns:
            The sub-trait instances.

        """
        raise NotImplementedError("I don't yet know how to get my sub_traits")

        for trait in []:
            if trait_type_filter is None or isinstance(trait, trait_type_filter):
                yield trait


    def __init__(self, archive, trait_key=None, object_id=None, parent_trait=None, loading='lazy'):
        super().__init__()
        self.archive = archive
        if object_id is not None:
            trait_key = trait_key.replace(object_id=object_id)
        self.trait_key = trait_key
        self.version = trait_key.version
        self.object_id = trait_key.object_id
        self._parent_trait = parent_trait
        self._trait_name = trait_key.trait_name

        self._sub_traits = TraitMapping()
        self._trait_cache = OrderedDict()


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
        self._realise()

    @property
    def trait_name(self):
        return self._trait_name


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

    def _trait_properties(self, trait_type=None):
        """Generator which iterates over the TraitProperties attached to this Trait.

        :param trait_type:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        Note that the descriptor must be handed this Trait object to actually retrieve
        data, which is why this is implemented as a private method. See
        `trait_property_values` as a simpler alternative.

        :returns: the TraitProperty descriptor object

        """

        if isinstance(trait_type, str):
            trait_type = tuple(trait_type)

        # Search class attributes:
        for key in dir(type(self)):
            obj = getattr(type(self), key)
            if isinstance(obj, TraitProperty):
                log.debug("Found trait property '{} of type'".format(key, obj.type))
                if (trait_type is None) or (obj.type in trait_type):
                    yield obj

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
            yield getattr(self, tp.name)

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
            primary_hdu = fits.PrimaryHDU(self.value)
            hdulist.append(primary_hdu)
        elif type(self).value.type in ("float", "int"):
            primary_hdu = fits.PrimaryHDU([self.value])
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
        # for trait_property in self.trait_property_values(['float.array', 'int.array']):
        #     extension = fits.ImageHDU(trait_property)
        #     hdulist.append(extension)

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


