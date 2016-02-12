import pytest

import numpy as np

from fidia.archive import MemoryArchive, BaseArchive
from fidia.archive.archive import Archive
from fidia.traits.utilities import TraitKey, TraitMapping, trait_property
from fidia.traits.base_traits import SpectralMap


class TestArchive:

    @pytest.fixture
    def example_spectral_map(self):

        class ExampleSpectralMap(SpectralMap):

            def __init__(self, archive, trait_key):
                self._object_id = trait_key.object_id
                super().__init__(trait_key)

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
                return np.random.random((3, 5, 10))
            @trait_property('float.array')
            def variance(self):
                return np.random.random((3, 5, 10))

        return ExampleSpectralMap

    @pytest.fixture
    def example_spectral_map_with_extra(self):

        class ExampleSpectralMapExtra(SpectralMap):

            def __init__(self, archive, trait_key):
                self._object_id = trait_key.object_id
                super().__init__(trait_key)

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
                return np.random.random((3, 5, 10))
            @trait_property('float.array')
            def variance(self):
                return np.random.random((3, 5, 10))
            @trait_property('float')
            def extra_value(self):
                return np.random.random()

        return ExampleSpectralMapExtra

    @pytest.fixture
    def example_spectral_map_with_extra_inherit(self, example_spectral_map):
        """Define a trait with an extra property."""
        class ExampleSpectralMap2(example_spectral_map):
            @trait_property('float')
            def extra_value(self):
                return np.random.random()
        return ExampleSpectralMap2

    @pytest.fixture
    def simple_archive(self, example_spectral_map, example_spectral_map_with_extra):

        class ExampleArchive(Archive):

            def __init__(self):
                self._contents = ['Gal1', 'Gal2']

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
                self.available_traits[TraitKey('spectral_map', None, None, None)] = example_spectral_map
                self.available_traits[TraitKey('spectral_map', 'extra', None, None)] = example_spectral_map_with_extra
                return self.available_traits

        return ExampleArchive

    # Basic Archive Functionality tests

    def test_can_create_simple_archive(self, simple_archive):
        simple_archive()

    def test_retrieve_correct_trait(self, simple_archive, example_spectral_map, example_spectral_map_with_extra):
        ar = simple_archive()
        assert ar.available_traits[TraitKey('spectral_map')] is example_spectral_map
        assert ar.available_traits[TraitKey('spectral_map', 'other')] is example_spectral_map
        assert ar.available_traits[TraitKey('spectral_map', 'extra')] is example_spectral_map_with_extra

    def test_trait_has_data(self, simple_archive):
        sample = simple_archive().get_full_sample()
        trait = sample['Gal1']['spectral_map']
        trait.value
        assert isinstance(trait.value, np.ndarray)

    def test_trait_inherited_has_parent_data(self, simple_archive):
        sample = simple_archive().get_full_sample()
        trait = sample['Gal1']['spectral_map', 'extra']
        trait.value
        assert isinstance(trait.value, np.ndarray)


    def test_trait_has_correct_schema(self, simple_archive):
        ar = simple_archive()
        trait = ar.available_traits[TraitKey('spectral_map', 'other')]
        schema = trait.schema()
        assert schema == {'value': 'float.array', 'variance': 'float.array'}

    def test_trait_extra_has_correct_schema(self, simple_archive):
        ar = simple_archive()
        trait = ar.available_traits[TraitKey('spectral_map', 'extra')]
        schema = trait.schema()
        print(trait.schema())
        assert schema == {'value': 'float.array', 'variance': 'float.array', 'extra_value': 'float'}


    def test_trait_inherited_has_correct_schema(self, example_spectral_map_with_extra_inherit):
        schema = example_spectral_map_with_extra_inherit.schema()
        assert schema == {'value': 'float.array', 'variance': 'float.array', 'extra_value': 'float'}

    def test_archive_has_correct_schema(self, simple_archive):
        ar = simple_archive()
        schema = ar.schema()
        assert schema == {'spectral_map': {'value': 'float.array', 'variance': 'float.array', 'extra_value': 'float'}}

    # Other tests.

    def test_create_inmemory_archive(self):
        m = MemoryArchive()
        assert isinstance(m, BaseArchive)

