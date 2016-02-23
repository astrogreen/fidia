import pickle
from io import BytesIO

from astropy.io import fits

from .abstract_base_traits import *
from ..exceptions import DataNotAvailable
from .utilities import TraitProperty

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

    def __init__(self, archive, trait_key, loading='lazy'):
        super().__init__()
        self.archive = archive
        self.trait_key = trait_key
        self.object_id = trait_key.object_id
        self._trait_name = trait_key.trait_name

        # The preload count is used to track how many accesses there are to this
        # trait so that it can be properly cleaned up when all loads are
        # complete.
        self._preload_count = 0

        if loading not in ('eager', 'lazy', 'verylazy'):
            raise ValueError("loading keyword must be one of ('eager', 'lazy', 'verylazy')")
        self._loading = loading

        self._trait_dict = dict()
        self._realise()

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

    def _trait_properties(self):
        """Generator which iterates over the TraitProperties attached to this Trait.

        Note that the descriptor must be handed this Trait object to actually retrieve
        data, which is why this is impelemented as a private method.

        :return: the TraitProperty descriptor object

        """
        # Search class attributes:
        for key in dir(type(self)):
            obj = getattr(type(self), key)
            if isinstance(obj, TraitProperty):
                log.debug("Found trait property '{}'".format(key))
                yield obj

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

    def export_fits(self, file):
        """FITS Exporter"""


        # Create a function holder which can be set to close the file if it is opened here
        file_cleanup = lambda x: None
        if isinstance(file, str):
            file = open(file, 'wb')
            # Store pointer to close function to be called at the end of the this function.
            file_cleanup = file.close

        hdulist = fits.HDUList(
            [fits.PrimaryHDU(self.value)]),

        for trait_property in self._trait_properties():
            if trait_property.name != 'value' and trait_property.type == "float.array":
                log.debug("Adding array '%s' to FITS output", trait_property.name)
                hdulist.append(getattr(self, trait_property.name))


        hdulist.writeto(file)

        # If necessary, close the open file handle.
        file_cleanup()

class Classification(Trait, AbstractBaseClassification): pass


