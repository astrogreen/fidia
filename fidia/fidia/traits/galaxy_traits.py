from .abstract_base_traits import *
from .base_traits import *

class StarFormationRate(Measurement): pass

class StellarMass(Measurement): pass

class VelocityMap(Map, Measurement): pass

class Abundance(Measurement): pass

class EmissionClassificationMap(AbstractBaseClassification, Map): pass

class PositionAngle(Measurement): pass