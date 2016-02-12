from .abstract_base_traits import *

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

class CachingTrait:
    def __init__(self, *args, **kwargs):
        super(CachingTrait, self).__init__()
        self._trait_dict = dict()
        self._realise()


    def _realise(self):
        """Search through the objects members for TraitProperties, and preload any found.

        """

        log.debug("Realising...")
        try:
            self.preload()
        except AttributeError:
            pass

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

        try:
            self.cleanup()
        except AttributeError:
            pass

    # def __enter__(self):
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     try:
    #         self.cleanup()
    #         self._cleaned_up = True
    #     except AttributeError:
    #         pass

class Measurement(AbstractMeasurement): pass

class Velocity(Measurement): pass

class Map(Base2DTrait):
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
    

class Spectrum(Base1DTrait, Measurement): pass

class Epoch(Measurement):

    @property
    def epoch(self):
        return self


class TimeSeries(Base1DTrait, Epoch): pass


class Image(Map): pass


class SpectralMap(Base3DTrait, CachingTrait):

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





