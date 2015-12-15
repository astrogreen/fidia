from .abstract_base_traits import *


class Measurement(AbstractMeasurement): pass


class Map(Base2DTrait): pass


class Spectrum(Base1DTrait, Measurement): pass

class Epoch(Measurement):

    @property
    def epoch(self):
        return self


class TimeSeries(Base1DTrait, Epoch): pass


class Image(Map): pass


class SpectralCube(Base3DTrait): pass





