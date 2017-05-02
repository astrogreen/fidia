from . import *

class StarFormationRate(Measurement):
    """Total rate of star formation"""
    pass

class StarFormationRateMap(Image):
    """Spatially resolved map of the star formation rate"""
    pass

class LineEmissionMap(Image):
    """Spatially-resolved map of line emission"""
    pass

class ExtinctionMap(Image):
    """Map of attenuation correction factor based on the Balmer decrement"""
    pass


class StellarMass(Measurement):
    """Mass in stars"""
    pass

class VelocityMap(Image, Measurement):
    """Spatially-resolved map(s) of velocity field(s) for each fitted kinematic component"""
    pass

class VelocityDispersionMap(VelocityMap):
    """Spatially-resolved map(s) of velocity dispersion(s) for each fitted kinematic component"""
    pass

class Abundance(Measurement): pass

class EmissionClassificationMap(Classification, Map):
    """Spatially-resolved classification of emission"""
    pass

class PositionAngle(Measurement):
    """Orientation of the object on the sky"""
    pass

class MorphologicalMeasurement(Measurement): pass