
# Standard Library Imports



# Other library imports
import astropy.coordinates
import astropy.wcs

# Internal package imports
from . import Trait
from .abstract_base_traits import *
from .trait_property import trait_property

# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


class SmartTrait(Trait):
    pass

class SkyCoordinate(astropy.coordinates.SkyCoord, SmartTrait):

    trait_type = 'sky_coordinate'

    def __init__(self, *args, **kwargs):
        SmartTrait.__init__(self, *args, **kwargs)
        astropy.coordinates.SkyCoord.__init__(self, self._ra(), self._dec(), unit='deg', frame=self._ref_frame)

    # @FIXME: explain why value is required here but not for WorldCoordinateSystem below.
    @trait_property('string')
    def value(self):
        return self.to_string('hmsdms')

    # @abstractproperty
    # def _ra(self):
    #     return NotImplementedError
    #
    # @abstractproperty
    # def _dec(self):
    #     return NotImplementedError

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

    @trait_property('string')
    def value(self):
        trim_lines = list(map(lambda x: x.strip(), repr(self.to_header()).splitlines()))
        return "\n".join(trim_lines)

    @abstractproperty
    def _wcs_string(self):
        return NotImplementedError

    def as_fits(self, file):
        # Not possible to create a FITS file for a WCS trait.
        # TODO: See if this method can be hidden or deleted.
        # TODO: Perhaps handle this by moving as_fits() off of the top level Trait class.
        return None
WorldCoordinateSystem.set_pretty_name("World Coordinate System")
WorldCoordinateSystem.set_short_name("WCS")
