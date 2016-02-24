
import numpy as np

from .archive import Archive
from ..traits.utilities import TraitKey, TraitMapping, trait_property
from ..traits.base_traits import SpectralMap
from ..exceptions import DataNotAvailable

class ExampleSpectralMap(SpectralMap):

    def init(self):
        if self.trait_name != 'mymap':
            raise DataNotAvailable("ExampleSpectraMap only has trait_name='mymap' data.")

    @classmethod
    def known_keys(cls, object_id):
        return TraitKey('spectral_map', 'mymap', None, object_id=object_id)

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

    @classmethod
    def known_keys(cls, object_id):
        return TraitKey('spectral_map', 'mymap', None, object_id=object_id)

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
        return self.available_traits
