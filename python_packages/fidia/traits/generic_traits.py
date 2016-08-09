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

