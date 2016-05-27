import pytest

import numpy as np

from fidia.archive import MemoryArchive, BaseArchive
from fidia.archive.archive import Archive
from fidia.traits.utilities import TraitKey, TraitMapping, trait_property
from fidia.traits import Trait, TraitProperty
from fidia.traits.base_traits import SpectralMap
from fidia.exceptions import DataNotAvailable
from fidia.archive.example_archive import ExampleArchive

from fidia.archive.example_archive import ExampleSpectralMap

class TestArchive:

    @pytest.fixture
    def example_spectral_map(self):

        class ExampleSpectralMap(SpectralMap):

            trait_type = 'spectral_map'

            def init(self):
                if self.trait_qualifier != 'mymap':
                    raise DataNotAvailable("ExampleSpectraMap only has 'mymap' data.")

            @classmethod
            def all_keys_for_id(cls, archive, object_id, parent_trait=None):
                return [TraitKey('spectral_map', 'mymap', None)]

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

        return ExampleSpectralMap

    @pytest.fixture
    def example_spectral_map_with_extra(self):

        class ExampleSpectralMapExtra(SpectralMap):

            trait_type = 'spectral_map'

            @classmethod
            def all_keys_for_id(cls, archive, object_id, parent_trait=None):
                return [TraitKey('spectral_map', 'mymap', None)]

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
    def example_archive(self):
        return ExampleArchive()

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
        trait = sample['Gal1']['spectral_map', 'mymap']
        trait.value()
        assert isinstance(trait.value(), np.ndarray)

    def test_trait_inherited_has_parent_data(self, simple_archive):
        sample = simple_archive().get_full_sample()
        trait = sample['Gal1']['spectral_map', 'extra']
        trait.value()
        assert isinstance(trait.value(), np.ndarray)


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


    def test_trait_inherited_has_correct_schema(self, simple_archive):
        ar = simple_archive()
        trait = ar.available_traits[TraitKey('spectral_map', 'extra')]
        schema = trait.schema()
        assert schema == {'value': 'float.array', 'variance': 'float.array', 'extra_value': 'float'}

    def test_archive_has_correct_schema(self, simple_archive):
        ar = simple_archive()
        schema = ar.schema()
        assert schema == {'spectral_map': {'value': 'float.array', 'variance': 'float.array', 'extra_value': 'float'}}

    # Other tests.

    def test_create_inmemory_archive(self):
        m = MemoryArchive()
        assert isinstance(m, BaseArchive)

    # Trait related tests:

    def test_trait_documentation(self, simple_archive):
        sample = simple_archive().get_full_sample()
        trait = sample['Gal1']['spectral_map', 'mymap']

        assert trait.value.doc == "TheSpectralMapDocumentation"

    def test_trait_property_list(self, simple_archive):
        sample = simple_archive().get_full_sample()
        trait = sample['Gal1']['spectral_map', 'mymap']
        for trait_property, expected in zip(trait._trait_properties(), ('value', 'variance')):
            assert trait_property.name == expected

    #
    # Schema related Tests
    #

    def test_get_type_for_trait_path(self, example_archive):
        assert isinstance(example_archive, Archive)
        assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait',)), Trait)
        assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait', 'value')), TraitProperty)
        assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait', 'sub_trait')), Trait)
        assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait', 'sub_trait', 'extra')), TraitProperty)
