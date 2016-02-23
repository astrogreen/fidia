
import numpy as np

from .archive import Archive
from ..traits.utilities import TraitKey, TraitMapping, trait_property
from ..traits.base_traits import SpectralMap
from ..exceptions import DataNotAvailable

class ExampleSpectralMap(SpectralMap):

    def __init__(self, archive, trait_key):
        self._object_id = trait_key.object_id
        if trait_key.trait_name != 'mymap':
            raise DataNotAvailable("ExampleSpectraMap only has 'mymap' data.")
        super().__init__(archive, trait_key)

    @classmethod
    def known_keys(cls, object_id):
        return TraitKey('spectral_map', 'mymap', None, object_id=object_id)

    def preload(self):
        # Make an object have typically the same random data.
        np.random.seed(hash(self._object_id) % 500000)
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

    def __init__(self, archive, trait_key):
        self._object_id = trait_key.object_id
        super().__init__(archive, trait_key)

    @classmethod
    def known_keys(cls, object_id):
        return TraitKey('spectral_map', 'mymap', None, object_id=object_id)

    def preload(self):
        # Make an object have typically the same random data.
        np.random.seed(hash(self._object_id) % 500000)
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

class TestMissingProperty(SpectralMap):

    @property
    def shape(self):
        return 0

    @classmethod
    def known_keys(cls, object_id):
        return TraitKey('spectral_map', 'mymap', None, object_id=object_id)

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
        return self.available_traits
