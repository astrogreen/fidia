from .abstract_base_traits import *

from . import Trait

# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()


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


class Redshift(Measurement): pass


class Magnitude(Measurement): pass


class Position(AbstractBaseArrayTrait): pass
# Should position be an array? Or some kind of "tuple"




class Spectrum(Measurement, AbstractBaseArrayTrait): pass

class Epoch(Measurement):

    @property
    def epoch(self):
        return self


class TimeSeries(Epoch, AbstractBaseArrayTrait): pass


class Image(Map):

    @property
    def shape(self):
        return self.value.value.shape


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


