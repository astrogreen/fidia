import pytest

import tempfile

import numpy as np

from fidia.archive import MemoryArchive, BaseArchive
from fidia.archive.archive import Archive, BasePathArchive
from fidia.traits.fidiacolumn import *
from fidia.traits import *
from fidia import traits
from fidia.exceptions import DataNotAvailable
from fidia.archive.example_archive import ExampleArchive

# from fidia.archive.example_archive import ExampleSpectralMap

import generate_test_data as testdata


@pytest.yield_fixture(scope='module')
def test_data_dir():

    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir



class TestArchiveAndColumns:

    @pytest.fixture
    def ArchiveWithColumns(self):

        class ArchiveWithColumns(BasePathArchive):
            _id = "testArchive"
            column_definitions = [
                ("col", FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0,
                                       ndim=2,
                                       timestamp=1))
                ]
        return ArchiveWithColumns

    # def test_archive_instance_columns_not_class_columns(self, ArchiveWithColumns):
    #     ar = ArchiveWithColumns(basepath='/')
    #
    #     assert ar.columns[0] is not ArchiveWithColumns.column_definitions[0]

    # def test_associated_columns_have_correct_association(self, ArchiveWithColumns):
    #     basepath = '/'
    #
    #     ar = ArchiveWithColumns(basepath=basepath)
    #     assert ar.columns.red_image._archive_id == ar.archive_id
    #     assert ar.columns.red_image._archive is ar

    # def test_instanciating_archive_doesnt_affect_class_columns(self):
    #
    #     class ArchiveWithColumns(BasePathArchive):
    #
    #         class columns:
    #             red_image = FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0,
    #                                        ndim=2)
    #
    #     class_column = ArchiveWithColumns.columns.red_image
    #     ar = ArchiveWithColumns(basepath='/')
    #     assert class_column is ArchiveWithColumns.columns.red_image
    #     assert class_column._archive_id is None
    #     assert class_column._archive is None

    def test_get_column_with_id(self, test_data_dir, ArchiveWithColumns):
        ar = ArchiveWithColumns(basepath=test_data_dir)  # type: fidia.archive.archive.Archive
        print(ar.archive_id)
        print(ar.columns._contents_by_alias.items())
        column = ar.columns["testArchive:fidia.traits.fidiacolumn.FITSDataColumn:" + \
                            "{object_id}/{object_id}_red_image.fits[0]:1"]

        assert isinstance(column, FIDIAColumn)

    def test_get_column_with_alias(self, test_data_dir, ArchiveWithColumns):
        ar = ArchiveWithColumns(basepath=test_data_dir)
        column = ar.columns["col"]

        assert isinstance(column, FIDIAColumn)

    def test_retrieve_data_from_path_column(self, test_data_dir, ArchiveWithColumns):
        ar = ArchiveWithColumns(basepath=test_data_dir)
        value = ar.columns["col"].get_value('Gal1')

        assert value.shape == (200, 200)



class TestExampleArchive:
    """Tests which are based on the Example Archive.

    These tests make much of the real, practical tests of the system, rather
    than being individual, 'unit' tests.

    """

    @pytest.fixture
    def example_archive(self, test_data_dir):
        return ExampleArchive(basepath=test_data_dir)

    def test_red_image_data(self, example_archive):
        img = example_archive.columns["red_image"].get_value('Gal1')
        assert img.shape == (200, 200)

    def test_red_image_exposed_data(self, example_archive):
        img = example_archive.columns["red_image_exposed"].get_value('Gal1')
        assert img in (3500, 3600, 2400)


    def test_example_archive_columns_available(self, example_archive):
        example_archive.columns


class TestArchive:

    pass
    # @pytest.fixture
    # def example_spectral_map(self):
    #
    #     return ExampleSpectralMap
    #
    # @pytest.fixture
    # def example_spectral_map_with_extra(self):
    #
    #     return ExampleSpectralMapExtra

    # @pytest.fixture
    # def example_spectral_map_with_extra_inherit(self, example_spectral_map):
    #     """Define a trait with an extra property."""
    #     class ExampleSpectralMap2(example_spectral_map):
    #         @trait_property('float')
    #         def extra_value(self):
    #             return np.random.random()
    #     return ExampleSpectralMap2



    # @pytest.fixture
    # def example_archive(self):
    #     return ExampleArchive()

    # @pytest.fixture
    # def simple_archive(self, example_spectral_map, example_spectral_map_with_extra):
    #
    #     class ExampleArchive(Archive):
    #
    #         def __init__(self):
    #             self._contents = ['Gal1', 'Gal2']
    #
    #             # Local cache for traits
    #             self._trait_cache = dict()
    #
    #             super().__init__()
    #
    #         @property
    #         def contents(self):
    #             return self._contents
    #
    #         @property
    #         def name(self):
    #             return 'ExampleArchive'
    #
    #         def define_available_traits(self):
    #             self.available_traits.register(example_spectral_map)
    #             self.available_traits.register(example_spectral_map_with_extra)
    #             return self.available_traits
    #
    #     return ExampleArchive

    # Basic Archive Functionality tests

    # def test_can_create_simple_archive(self, simple_archive):
    #     simple_archive()

    # def test_retrieve_correct_trait(self, simple_archive, example_spectral_map, example_spectral_map_with_extra):
    #     # ar = simple_archive()
    #     # assert ar.available_traits.retrieve_with_key(TraitKey('spectral_map')) is example_spectral_map
    #     # assert ar.available_traits.retrieve_with_key(TraitKey('spectral_map', branch='other')) is example_spectral_map
    #     # assert ar.available_traits.retrieve_with_key(TraitKey('spectral_map', branch='extra')) is example_spectral_map_with_extra
    #     pass

    # def test_trait_has_data(self, simple_archive):
    #     # sample = simple_archive().get_full_sample()
    #     # trait = sample['Gal1']['spectral_map']
    #     # trait.value()
    #     # assert isinstance(trait.value(), np.ndarray)
    #     pass

    # def test_trait_inherited_has_parent_data(self, simple_archive):
    #     # sample = simple_archive().get_full_sample()
    #     # trait = sample['Gal1'][TraitKey(trait_type='spectral_map', branch='extra')]
    #     # trait.value()
    #     # assert isinstance(trait.value(), np.ndarray)
    #     pass

    # def test_trait_has_correct_schema(self, simple_archive):
    #     # ar = simple_archive()
    #     # trait = ar.available_traits.retrieve_with_key(TraitKey('spectral_map', branch='other'))
    #     # schema = trait.schema()
    #     # assert schema == {'value': 'float.array.3', 'variance': 'float.array.3'}
    #     pass

    # def test_trait_extra_has_correct_schema(self, simple_archive):
    #     ar = simple_archive()
    #     trait = ar.available_traits.retrieve_with_key(TraitKey('spectral_map', branch='extra'))
    #     schema = trait.schema()
    #     print(trait.schema())
    #     assert schema == {'value': 'float.array.3', 'variance': 'float.array.3', 'extra_value': 'float'}

    # def test_trait_inherited_has_correct_schema(self, simple_archive):
    #     ar = simple_archive()
    #     trait = ar.available_traits.retrieve_with_key(TraitKey('spectral_map', branch='extra'))
    #     schema = trait.schema()
    #     assert schema == {'value': 'float.array.3', 'variance': 'float.array.3', 'extra_value': 'float'}
    #
    # def test_archive_has_correct_schema(self, simple_archive):
    #     ar = simple_archive()
    #     schema_by_trait_type = ar.schema(by_trait_name=False)
    #     assert schema_by_trait_type == {'spectral_map': {None: {
    #         'value': 'float.array.3', 'variance': 'float.array.3', 'extra_value': 'float'}}}
    #
    #     schema_by_trait_name = ar.schema(by_trait_name=True)
    #     assert schema_by_trait_name == {'spectral_map': {
    #         'value': 'float.array.3', 'variance': 'float.array.3', 'extra_value': 'float'}}
    #
    # def test_all_object_traits_in_schema(self, simple_archive):
    #     ar = simple_archive()
    #     schema_by_trait_type = ar.schema(by_trait_name=False)
    #     schema_by_trait_name = ar.schema(by_trait_name=True)
    #     sample = ar.get_full_sample()
    #     for astro_object in sample:
    #         trait_key_list = sample[astro_object].keys()
    #         for tk in trait_key_list:
    #             assert tk.trait_name in schema_by_trait_name
    #             assert tk.trait_type in schema_by_trait_type

    # Other tests.

    # def test_create_inmemory_archive(self):
    #     m = MemoryArchive()
    #     assert isinstance(m, BaseArchive)
    #
    # # Trait related tests:
    #
    # def test_trait_documentation(self, simple_archive):
    #     sample = simple_archive().get_full_sample()
    #     trait = sample['Gal1']['spectral_map:other']
    #
    #     assert trait.value.doc == "TheSpectralMapDocumentation"
    #
    # def test_trait_property_list(self, simple_archive):
    #     sample = simple_archive().get_full_sample()
    #     trait = sample['Gal1']['spectral_map:other']
    #     for trait_property, expected in zip(trait._trait_properties(), ('value', 'variance')):
    #         assert trait_property.name == expected
    #
    # # Feature data functionality
    #
    # def test_archive_has_feature_data(self, example_archive):
    #     # type: (ExampleArchive) -> None
    #     assert example_archive.feature_catalog_data is not None
    #
    #     for elem in example_archive.feature_catalog_data:
    #         assert isinstance(elem, TraitPath)
    #
    #
    # #
    # # Schema related Tests
    # #
    #
    # def test_get_type_for_trait_path(self, example_archive):
    #     assert isinstance(example_archive, Archive)
    #     assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait',)), Trait)
    #     assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait', 'value')), TraitProperty)
    #     assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait', 'sub_trait')), Trait)
    #     assert issubclass(example_archive.type_for_trait_path(('simple_heir_trait', 'sub_trait', 'extra')), TraitProperty)
    #
    # def test_schema_for_traits_with_qualifiers_differs(self, example_archive):
    #     schema = example_archive.schema(by_trait_name=False)
    #
    #     assert 'extra_property_blue' in schema['image']['blue']
    #     assert 'extra_property_blue' not in schema['image']['red']
    #     assert 'extra_property_red' in schema['image']['red']
    #     assert 'extra_property_red' not in schema['image']['blue']
    #
    # def test_schema_for_subtraits_with_qualifiers_differs(self, example_archive):
    #     schema = example_archive.schema(by_trait_name=False)
    #
    #     sub_schema = schema['image']['blue']
    #     assert 'extra_property_blue' in sub_schema['image']['blue']
    #     assert 'extra_property_blue' not in sub_schema['image']['red']
    #     assert 'extra_property_red' in sub_schema['image']['red']
    #     assert 'extra_property_red' not in sub_schema['image']['blue']
