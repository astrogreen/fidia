from . import *

class StarFormationRate(Measurement): pass

class StellarMass(Measurement): pass

class VelocityMap(Image, Measurement):
    """A spatially resolved map of velocities across an object."""
    pass

class VelocityDispersionMap(VelocityMap):
    """A spatially resolved map of velocity dispersions across an object."""
    pass

class Abundance(Measurement): pass

class EmissionClassificationMap(Classification, Map): pass

class PositionAngle(Measurement): pass

class MorphologicalMeasurement(Measurement): pass