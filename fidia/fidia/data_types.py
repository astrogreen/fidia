from astropy.units import Quantity
from numpy import ndarray


class FidiaDataType(object):

    @property
    def units(self):
        return self._units
    @units.setter
    def units(self, value):
        if isinstance(value, Quantity):
            self._units = value
        else:
            raise ValueError("Not a valid unit")


class FidiaArrayDataType(FidiaDataType):

    def __init__(self):
        super(FidiaArrayDataType, self).__init__()
        self._data = None

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        if isinstance(value, ndarray):
            self._data = value
        else:
            raise ValueError("data must be a numpy array.")

    def __call__(self):
        return self.data




class Map(FidiaArrayDataType):
    """docstring for Map"""
    def __init__(self):
        super(Map, self).__init__()
    
    @property
    def coordinates(self):
        return self._coordinates
    @coordinates.setter
    def coordinates(self):
        if self._data:
            pass

class IrregularMap(Map):
    pass

class RegularMap(Map):
    pass


class Spectrum(FidiaDataType):
    def __init__(self):
        super(Spectrum, self).__init__()

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        pass
        


class fProperty(FidiaDataType):
    def __init__(self):
        pass

