from . import *

class StarFormationRate(Measurement):
    """Total rate of star formation"""
    pass

class StarFormationRateMap(Image):
    """Spatially-resolved map of the rate of star formation"""
    pass

class LineEmissionMap(Image):
    """Spatially-resolved map of line emission"""
    pass

class ExtinctionMap(Image):
    """Spatially-resolved map of extinction"""
    pass


class StellarMass(Measurement):
    """Mass in stars"""
    pass

class VelocityMap(Image, Measurement):
    """A spatially-resolved map of velocities across an object"""
    pass

class VelocityDispersionMap(VelocityMap):
    """A spatially-resolved map of velocity dispersions across an object"""
    pass

class Abundance(Measurement): pass

class EmissionClassificationMap(Classification, Map):
    """Spatially-resolved classification of emission"""
    pass

class PositionAngle(Measurement):
    """Orientation of the object on the sky"""
    pass

class MorphologicalMeasurement(Measurement): pass