from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from fidia.traits import Trait, TraitProperty, TraitKey, TraitPath
from fidia.archive import example_archive

from fidia.descriptions import TraitDescriptionsMixin

from fidia.traits import validate_trait_name


class TestTraits:

    @pytest.fixture
    def TestTrait(self):
        class TestTrait(Trait):
            value = TraitProperty(dtype=(int), n_dim=0, optional=False)
            optional_value = TraitProperty(dtype=(int), n_dim=0, optional=True)

        return TestTrait


    def test_get_trait_properties(self, TestTrait):

        for attr in TestTrait._trait_property_slots():
            prop = getattr(TestTrait, attr)
            assert isinstance(prop, TraitProperty)

    @pytest.mark.xfail
    def test_trait_schema(self):
        """This test checks both versions of the schema."""
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'), object_id='1')

        # Test the schema by trait_type
        schema_by_trait_type = test_trait.schema(by_trait_name=False)

        assert isinstance(schema_by_trait_type, dict)

        assert 'value' in schema_by_trait_type
        assert schema_by_trait_type['value'] == 'float'
        assert 'extra' in schema_by_trait_type
        assert schema_by_trait_type['extra'] == 'string'

        del schema_by_trait_type

        # Test the schema by trait_name
        schema_by_trait_name = test_trait.schema(by_trait_name=True)

        assert isinstance(schema_by_trait_name, dict)

        assert 'value' in schema_by_trait_name
        assert schema_by_trait_name['value'] == 'float'
        assert 'extra' in schema_by_trait_name
        assert schema_by_trait_name['extra'] == 'string'

    @pytest.mark.xfail
    def test_trait_schema_with_subtraits(self):

        test_trait = example_archive.SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'), object_id='1')

        # Test the schema by trait_type
        schema_by_trait_type = test_trait.schema(by_trait_name=False)

        assert isinstance(schema_by_trait_type, dict)

        assert 'value' in schema_by_trait_type
        assert schema_by_trait_type['value'] == 'float'
        assert 'extra' in schema_by_trait_type
        assert schema_by_trait_type['extra'] == 'string'

        # Hierarchical part of schema:
        assert 'sub_trait' in schema_by_trait_type
        assert isinstance(schema_by_trait_type['sub_trait'], dict)
        assert isinstance(schema_by_trait_type['sub_trait'][None], dict)
        assert 'value' in schema_by_trait_type['sub_trait'][None]

        del schema_by_trait_type

        # Test the schema by trait_name
        schema_by_trait_name = test_trait.schema(by_trait_name=True)

        assert isinstance(schema_by_trait_name, dict)

        assert 'value' in schema_by_trait_name
        assert schema_by_trait_name['value'] == 'float'
        assert 'extra' in schema_by_trait_name
        assert schema_by_trait_name['extra'] == 'string'

        # Hierarchical part of schema:
        assert 'sub_trait' in schema_by_trait_name
        assert isinstance(schema_by_trait_name['sub_trait'], dict)
        assert isinstance(schema_by_trait_name['sub_trait'], dict)
        assert 'value' in schema_by_trait_name['sub_trait']

    @pytest.mark.xfail
    def test_trait_schema_catalog_non_catalog(self):

        test_trait = example_archive.SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'), object_id='1')

        # This only tests the schema by trait_name

        schema_by_catalog = test_trait.schema(by_trait_name=True, data_class='catalog')

        assert 'value' in schema_by_catalog
        assert 'extra' in schema_by_catalog
        assert 'non_catalog_data' not in schema_by_catalog

        # Hierarchical part of schema:
        assert 'sub_trait' in schema_by_catalog
        assert 'value' in schema_by_catalog['sub_trait']
        assert 'extra' in schema_by_catalog['sub_trait']
        assert 'non_catalog_data' not in schema_by_catalog['sub_trait']

        del schema_by_catalog


        schema_by_non_catalog = test_trait.schema(by_trait_name=True, data_class='non-catalog')

        assert 'value' not in schema_by_non_catalog
        assert 'extra' not in schema_by_non_catalog
        assert 'non_catalog_data' in schema_by_non_catalog

        # Hierarchical part of schema:
        assert 'sub_trait' in schema_by_non_catalog
        assert 'value' not in schema_by_non_catalog['sub_trait']
        assert 'extra' not in schema_by_non_catalog['sub_trait']
        assert 'non_catalog_data' in schema_by_non_catalog['sub_trait']

    # @pytest.mark.xfail
    # def test_trait_schema_catalog_non_catalog_trims_empty(self):
    #
    #     # This only tests the schema by trait_name
    #
    #     class SimpleTraitWithSubtraits(Trait):
    #         # NOTE: Tests rely on this class, so changing it will require updating the tests!
    #
    #         trait_type = "simple_heir_trait"
    #
    #         sub_traits = TraitRegistry()
    #
    #         @sub_traits.register
    #         class SubTrait(example_archive.SimpleTrait):
    #             trait_type = 'sub_trait'
    #
    #         @sub_traits.register
    #         class CatalogSubTrait(Trait):
    #             trait_type ='sub_trait_catalog_only'
    #
    #             @trait_property('float')
    #             def value(self):
    #                 return 1.0
    #
    #         @sub_traits.register
    #         class NonCatalogSubTrait(Trait):
    #             trait_type = 'sub_trait_non_catalog_only'
    #
    #             @trait_property('float.array.1')
    #             def value(self):
    #                 return [1.0, 2.0]
    #
    #         @trait_property('float')
    #         def value(self):
    #             return 5.5
    #
    #         @trait_property('float.array.1')
    #         def non_catalog_data(self):
    #             return [1.1, 2.2, 3.3]
    #
    #         @trait_property('string')
    #         def extra(self):
    #             return "Extra info"
    #
    #     test_trait = SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'),
    #                                           object_id='1')
    #
    #     # Test the catalog-only version of the schema:
    #
    #     schema_by_catalog = test_trait.schema(by_trait_name=True, data_class='catalog')
    #
    #     # Hierarchical part of schema:
    #     assert 'sub_trait_non_catalog_only' not in schema_by_catalog
    #     assert 'sub_trait_catalog_only' in schema_by_catalog
    #
    #     del schema_by_catalog
    #
    #     # Test the non-catalog version of the schema:
    #
    #     schema_by_non_catalog = test_trait.schema(by_trait_name=True, data_class='non-catalog')
    #
    #     # Hierarchical part of schema:
    #     assert 'sub_trait_non_catalog_only' in schema_by_non_catalog
    #     assert 'sub_trait_catalog_only' not in schema_by_non_catalog


    @pytest.mark.xfail   # @TODO: Failing because sub-traits not implemented
    def test_retrieve_sub_trait_by_dictionary(self):

        test_trait = example_archive.SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'),
                                                                  object_id='1')

        assert isinstance(test_trait['sub_trait'], Trait)

    @pytest.mark.xfail   # @TODO: Failing because descriptions/metadata not implemented
    def test_trait_descriptions(self):
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'), object_id='1')

        assert hasattr(test_trait, 'get_pretty_name')
        assert hasattr(test_trait, 'get_documentation')
        assert hasattr(test_trait, 'get_description')

        assert test_trait.get_description() == "Description for SimpleTrait."

    @pytest.mark.xfail   # @TODO: Failing because descriptions/metadata not implemented
    def test_trait_property_descriptions(self):

        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'), object_id='1')

        # Check that a trait property has the necessary description attributes
        assert hasattr(test_trait.value, 'get_pretty_name')
        assert hasattr(test_trait.value, 'get_documentation')
        assert hasattr(test_trait.value, 'get_description')
        assert hasattr(test_trait.value, 'get_short_name')

        # Check that descriptions are set correctly:
        assert test_trait.value.get_description() == "TheValue"
        assert test_trait.non_catalog_data.get_description() == "Some Non-catalog data"
        assert test_trait.extra.get_description() == "ExtraInformation"

        # Check that descriptions are set correctly:
        assert test_trait.value.get_pretty_name() == "Value"
        assert test_trait.non_catalog_data.get_pretty_name() == "Non-catalog Data"
        assert test_trait.extra.get_pretty_name() == "Extra Info"


    @pytest.mark.xfail   # @TODO: Failing because descriptions/metadata not implemented
    def test_trait_documentation(self):
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey.as_traitkey('test_trait:default(ver0)'), object_id='1')

        print(type(test_trait.get_documentation))
        print(test_trait.get_documentation())
        assert "Extended documentation" in test_trait.get_documentation()
        # The description should not be in the documentation
        assert test_trait.get_description() not in test_trait.get_documentation()
        assert test_trait._documentation_format == 'markdown'

        assert "<strong>text</strong>" in test_trait.get_documentation('html')


class TestSpecificTraitsInArchives:

    @pytest.fixture
    def example_archive(self):
        return example_archive.ExampleArchive()

    @pytest.fixture
    def example_sample(self, example_archive):
        return example_archive.get_full_sample()

    @pytest.fixture
    def a_astro_object(self, example_sample):
        return example_sample['Gal1']


    def test_PixelImage_trait(self, a_astro_object):
        """Test of the PixelImage Trait (and indirectly, the RawFileColumn Column)."""

        from PIL import Image as PILImage

        img = a_astro_object.pixel_image['spectra']

        assert hasattr(img, 'bytes')

        assert isinstance(img.image, PILImage.Image)


class TestTraitKeys:


    @pytest.fixture
    def valid_traitkey_list(self):
        return [
            ('my_trait', 'branch', 'ver'),
            ('my_trait', 'branch', 'v0.3'),
            ('my_trait', 'branch', '0.5'),
            ('my_trait', 'branch', '135134'),
            ('my_trait', 'b1.2', 'ver'),
            ('my_trait', '1.3', 'ver'),
            ('my_trait', 'other_branch', 'ver'),
            ('my_trait', 'branch', 'v1_3_5'),
            ('emission_map', None, 'v1'),
            ('emission_map', None, None),
            ('emission_map', 'b1', None)
        ]

    def test_traitkey_fully_qualified(self, valid_traitkey_list):

        # Check a selection of fully defined TraitKeys are valid (i.e. they don't raise an error)
        for t in valid_traitkey_list:
            if not None in t:
                print(t)
                TraitKey(*t)

        # Check that invalid TraitKeys raise an error on construction
        invalid_trait_types = ("3band", "my-trait")
        for t in invalid_trait_types:
            with pytest.raises(ValueError):
                print(t)
                TraitKey(t, "v0.3")

    def test_traitkey_string_construction(self):
        # Check that TraitKeys can be constructed from their strings
        TraitKey.as_traitkey("gama:stellar_masses(v0.3)")

    def test_string_traitkeys_reconstruction(self, valid_traitkey_list):
        for tk_tuple in valid_traitkey_list:
            tk = TraitKey(*tk_tuple)
            print(tk)
            assert TraitKey.as_traitkey(str(tk)) == tk

    def test_hyphen_string_roundtrip(self, valid_traitkey_list):
        for t in valid_traitkey_list:
            tk = TraitKey(*t)
            print(tk)
            hyphen_str = tk.ashyphenstr()
            print(hyphen_str)
            assert TraitKey.as_traitkey(hyphen_str) == tk

    def test_trait_key_hyphen_str_construction(self, valid_traitkey_list):
        # Check that TraitKeys can be created from their hyphen string notation:
        for t in valid_traitkey_list:
            trait_key_string = "-".join(map(str, t)).replace('None', '')
            print(trait_key_string)
            assert TraitKey.as_traitkey(trait_key_string) == TraitKey(*t)


    def test_traitkey_string_forms(self):

        test_list = [
            (TraitKey('my_trait'), 'my_trait'),
            (TraitKey('my_trait', version='v2'), 'my_trait(v2)'),
            (TraitKey('my_trait', branch='b2'), 'my_trait:b2')
        ]

        for tk, string_representation in test_list:
            assert str(tk) == string_representation

    def test_traitkey_not_fully_qualified(self):
        TraitKey('my_trait')
        TraitKey('my_trait', branch='b1')
        TraitKey('my_trait', version='v1')


    def test_convenience_trait_key_validation_functions(self):


        with pytest.raises(ValueError):
            validate_trait_name("blah:fsdf")

        with pytest.raises(ValueError):
            validate_trait_name("3var")

        with pytest.raises(ValueError):
            validate_trait_name("line_map-blue")

        validate_trait_name("blue_line_map")


class TestTraitPaths:

    def test_trait_path_creation(self):

        # Basic creation: elements are fully qualified TraitKeys
        tp = TraitPath([TraitKey("my_type"), TraitKey("my_sub_type")])
        assert isinstance(tp, TraitPath)
        for i in tp:
            assert isinstance(i, TraitKey)
        assert len(tp) == 2


        # creation from string trait_keys
        tp = TraitPath(["image-r", "wcs"])
        assert isinstance(tp, TraitPath)
        for i in tp:
            assert isinstance(i, TraitKey)
        assert len(tp) == 2


        # creation from path string
        tp = TraitPath("image-r/wcs")
        assert isinstance(tp, TraitPath)
        for i in tp:
            assert isinstance(i, TraitKey)
        assert len(tp) == 2

