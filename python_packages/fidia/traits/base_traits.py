import pickle
from io import BytesIO

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
        self._trait_key = trait_key
        self.object_id = trait_key.object_id
        self._trait_name = trait_key.trait_name

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

    def _realise(self):
        """Search through the objects members for TraitProperties, and preload any found.


        """

        log.debug("Realising...")

        # @TODO: The try/except block here is messy, and probably would catch things it's not supposed to.

        try:
            self.preload()

            # Search class attributes:
            for key in type(self).__dict__:
                obj = type(self).__dict__[key]
                if isinstance(obj, TraitProperty):
                    log.debug("Found trait data on class '{}'".format(key))
                    self._trait_dict[key] = obj.fload(self)
            # Search instance attributes:
            for key in self.__dict__:
                obj = self.__dict__[key]
                if isinstance(obj, TraitProperty):
                    log.debug("Found trait data on instance'{}'".format(key))
                    self._trait_dict[key] = obj.fload(self)
        except DataNotAvailable:
            raise
        except:
            raise DataNotAvailable("Error in preload for trait '%s'" % self.__class__)
        finally:
            try:
                self.cleanup()
            except:
                pass

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

    def name(self):
        raise NotImplementedError

    def value(self):
        raise NotImplementedError

    def variance(self):
        raise NotImplementedError

    def covariance(self):
        raise NotImplementedError

    def weight(self):
        raise NotImplementedError


class Classification(Trait, AbstractBaseClassification): pass


