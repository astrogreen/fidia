
import numpy as np

from .archive import Archive
from ..traits.utilities import TraitKey, TraitMapping, trait_property
from ..traits.base_traits import SpectralMap, Image, Measurement
from ..exceptions import DataNotAvailable

class ExampleSpectralMap(SpectralMap):

    # def init(self):
    #     if self.trait_name != 'mymap':
    #         raise DataNotAvailable("ExampleSpectraMap only has trait_name='mymap' data.")

    def preload(self):
        # Make an object have typically the same random data.
        np.random.seed(hash(self.object_id) % 500000)
        self._clean = False

    def cleanup(self):
        self._clean = True

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        """TheSpectralMapDocumentation"""
        assert not self._clean
        return np.random.random((3, 5, 10))
    @trait_property('float.array')
    def variance(self):
        assert not self._clean
        return np.random.random((3, 5, 10))


class ExampleSpectralMapExtra(SpectralMap):

    def preload(self):
        # Make an object have typically the same random data.
        np.random.seed(hash(self.object_id) % 500000)
        self._clean = False

    def cleanup(self):
        self._clean = True

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        assert not self._clean
        return np.random.random((3, 5, 10))
    @trait_property('float.array')
    def variance(self):
        assert not self._clean
        return np.random.random((3, 5, 10))
    @trait_property('float')
    def extra_value(self):
        assert not self._clean
        return np.random.random()

    @trait_property('string')
    def galaxy_name(self):
        assert not self._clean
        return self.object_id

class VelocityMap(Image):

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        return np.random.random((5, 5))
        #return np.random.random((50, 50))

    @trait_property('float.array')
    def variance(self):
        return np.random.random((5, 5))

class LineMap(Image):

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.ndarray')
    def value(self):
        return np.random.random((5, 5))

    @trait_property('float.ndarray')
    def variance(self):
        return np.random.random((5, 5))

class Redshift(Measurement):

    @trait_property('float')
    def value(self):
        return 3.14159

    def unit(self):
        return None

class TestMissingProperty(SpectralMap):

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        return np.random.random((3, 5, 10))
    @trait_property('float.array')
    def variance(self):
        return np.random.random((3, 5, 10))

    @trait_property('string')
    def galaxy_name(self):
        return self.object_id

class ExampleArchive(Archive):

    def __init__(self):
        self._contents = ['Gal1', 'Gal2', 'Gal3']

        # Local cache for traits
        self._trait_cache = dict()

        super().__init__()

    @property
    def contents(self):
        return self._contents

    @property
    def name(self):
        return 'ExampleArchive'

    def define_available_traits(self):
        self.available_traits[TraitKey('spectral_map', None, None, None)] = ExampleSpectralMap
        self.available_traits[TraitKey('spectral_map', 'extra', None, None)] = ExampleSpectralMapExtra
        self.available_traits[TraitKey('spectral_map', 'extra', None, 'Gal2')] = TestMissingProperty
        self.available_traits[TraitKey('line_map', None, None, None)] = LineMap
        self.available_traits[TraitKey('velocity_map', None, None, None)] = VelocityMap
        self.available_traits[TraitKey('redshift', None, None, None)] = Redshift

        return self.available_traits
