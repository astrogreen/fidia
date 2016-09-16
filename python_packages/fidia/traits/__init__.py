from .base_trait import Trait

from .smart_traits import WorldCoordinateSystem, SkyCoordinate

from .generic_traits import Measurement, TimeSeries, SpectralMap, Map, Map2D, Image, \
    Classification, ClassificationMap, FlagMap, Redshift

from .catalog_traits import catalog_trait

from .meta_data_traits import MetadataTrait, \
    OpticalTelescopeCharacteristics, DetectorCharacteristics, SpectrographCharacteristics

from .galaxy_traits import VelocityMap, MorphologicalMeasurement

from .trait_property import TraitProperty, trait_property
from .trait_key import TraitKey, \
    validate_trait_type, validate_trait_qualifier, validate_trait_branch, validate_trait_version, \
    validate_trait_name
from .trait_registry import TraitRegistry
