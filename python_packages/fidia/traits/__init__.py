from .base_trait import Trait, TraitCollection

# from .smart_traits import WorldCoordinateSystem, SkyCoordinate
#
# from .generic_traits import *
#
# from .catalog_traits import catalog_trait
#
# from .meta_data_traits import MetadataTrait, \
#     OpticalTelescopeCharacteristics, DetectorCharacteristics, SpectrographCharacteristics
#
# from .galaxy_traits import VelocityMap, VelocityDispersionMap, MorphologicalMeasurement, StarFormationRateMap, \
#     LineEmissionMap, ExtinctionMap
#
# from .references import ColumnReference, TraitMapping
#
from .trait_property import TraitProperty, trait_property
from .trait_key import TraitKey, TraitPath, \
    validate_trait_name, validate_trait_branch, validate_trait_version, \
    validate_trait_name
from .trait_registry import TraitRegistry

from .references import *
