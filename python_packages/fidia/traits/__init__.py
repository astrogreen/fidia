from .base_traits import \
    Trait, Measurement, TimeSeries, SpectralMap, Map, Image, WorldCoordinateSystem, SkyCoordinate, \
    OpticalTelescopeCharacteristics, DetectorCharacteristics, SpectrographCharacteristics
from .galaxy_traits import VelocityMap

from .utilities import TraitProperty, trait_property, TraitKey
from .trait_registry import TraitRegistry
