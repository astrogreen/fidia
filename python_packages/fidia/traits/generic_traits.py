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


class ClassificationMap(Trait):

    valid_classifications = None

