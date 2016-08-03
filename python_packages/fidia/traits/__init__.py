from .base_trait import Trait

from .smart_traits import WorldCoordinateSystem, SkyCoordinate

from .generic_traits import Measurement, TimeSeries, SpectralMap, Map, Image, Classification

from .meta_data_traits import OpticalTelescopeCharacteristics, DetectorCharacteristics, SpectrographCharacteristics

from .galaxy_traits import VelocityMap

from .utilities import TraitProperty, trait_property, TraitKey
from .trait_registry import TraitRegistry
