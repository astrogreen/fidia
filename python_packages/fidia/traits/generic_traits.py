from .abstract_base_traits import *

from . import Trait
from .base_trait import FITSExportMixin

import numpy as np

from cached_property import cached_property

# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()


# class Measurement(Trait, AbstractMeasurement): pass
class Measurement(Trait): pass


class Velocity(Measurement): pass

class Redshift(Trait): pass

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

class Map2D(Map, FITSExportMixin):
    """A Trait who's value can be displayed as a contiguous 2D image of square pixels."""
    pass

class MetadataTrait(Trait):
    def __init__(self, *args, **kwargs):
        super(MetadataTrait, self).__init__(*args, **kwargs)




class DetectorCharacteristics(MetadataTrait):
    """Metadata describing the characteristics of the detector used"""

    required_trait_properties = {
        'detector_id': 'string',
        'detector_size': 'string',
        'gain': 'float',
        'read_noise': 'float'
    }

class SpectrographCharacteristics(Trait):
    """Metadata describing the characteristics of the spectrograph used"""

    pass

class OpticalTelescopeCharacteristics(Trait):
    """Metadata describing the characteristics of the optical telescope used"""
    pass



class Spectrum(Measurement, AbstractBaseArrayTrait): pass

class Epoch(Measurement):

    @property
    def epoch(self):
        return self


class TimeSeries(Epoch, AbstractBaseArrayTrait): pass


class Image(Map2D):

    @property
    def shape(self):
        return self.value.value.shape


class SpectralMap(Trait, AbstractBaseArrayTrait, FITSExportMixin):
    """Spatially-resolved collection of spectra"""

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


class ClassificationMap(Map2D):
    """Spatially-resolved collection of classifications"""

    valid_classifications = None

class FlagMap(Map2D):
    """Spatially-resolved collection of data flags"""

    valid_flags = None

    @cached_property
    def flag_names(self):
        # type: () -> List
        return [i[0] for i in self.valid_flags]

    @property
    def shape(self):
        return self.value().shape

    def mask(self, flag):
        """Return a numpy mask array that is true where the given flag is set."""

        if flag not in self.flag_names:
            raise ValueError("%s is not a valid flag for the FlagMap %s" % (flag, self))

        return 0 != np.bitwise_and(self.value(), np.uint64(2**(self.flag_names.index(flag))))

    def n_flags(self):
        """Return an array showing the number of flags set at each pixel in the map."""
        n_flags = np.zeros(self.vaule.shape(), dtype=np.int32)
        for flag in self.flag_names:
            n_flags += self.mask(flag).astype(np.int)

        return n_flags

