from astropy.units import Quantity
from numpy import ndarray


class FidiaDataType(object):
    """The fundamental FIDIA data type.

    All other data types should be derived from this class.

    """


    @property
    def units(self):
        return self._units
    @units.setter
    def units(self, value):
        if isinstance(value, Quantity):
            self._units = value
        elif value is None:
            # The units can be not set.
            self._units = value            
        else:
            raise ValueError("Not a valid unit")

    @property
    def ucd(self):
        return self._ucd

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
    """Spatially resolved information about an object.

    What are maps?
    --------------

    - Images in broad or narrow bands
    - Maps measured properties at each spatial location in a galaxy




    """
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
        


class Property(FidiaDataType):
    """A generic numeric property of an object, single value.

    """
    def __init__(self):
        pass


#  _____  _           _                       _              
# |  __ \| |         | |                     | |             
# | |__) | |__   ___ | |_ ___  _ __ ___   ___| |_ _ __ _   _ 
# |  ___/| '_ \ / _ \| __/ _ \| '_ ` _ \ / _ \ __| '__| | | |
# | |    | | | | (_) | || (_) | | | | | |  __/ |_| |  | |_| |
# |_|    |_| |_|\___/ \__\___/|_| |_| |_|\___|\__|_|   \__, |
#                                                       __/ |
#                                                      |___/ 

class Magnitude(Property):
    """A magnitude in the typical astronomical sense."""

    def __init__(self, value):
        self._value = value






class Color(Property):
    """A color derived from magnitudes, e.g. g-i."""

    def __init__(self, value, first_band, second_band):
        
        self._value = value
        self._ucd = "phot.color"
        # @TODO: Put correct units here from Quantities package
        self._units = "magnitudes"








