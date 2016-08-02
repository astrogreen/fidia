from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from fidia.traits.abstract_base_traits import *
from fidia.traits.base_traits import Trait
from fidia.traits import TraitProperty, trait_property, TraitKey, TraitRegistry
from fidia.archive import example_archive

from fidia.descriptions import TraitDescriptionsMixin

from fidia.traits.utilities import validate_trait_name, validate_trait_type

def test_incomplete_trait_fails():

    class InvalidTestTrait(AbstractBaseTrait):

        @property
        def value(self):
            return 5

    with pytest.raises(TypeError):
        InvalidTestTrait()

    class ValidTestTrait(AbstractBaseTrait):

        def schema(cls):
            return []

        @property
        def value(self):
            return 5

        @property
        def description(self):
            return 5

        @property
        def data_type(self):
            return None

        @property
        def reference(self):
            return None

    ValidTestTrait()

class TestTraits:

    # @pytest.fixture
    # def TestTrait(self):
    #
    #     class TestTrait(Trait):
    #
    #         @trait_property('float')
    #         def value(self):
    #             return 5.5
    #
    #         @trait_property('string')
    #         def extra(self):
    #             return "Extra info"
    #
    #     return TestTrait
    #
    # @pytest.fixture
    # def TestTraitWithSubTrait(self):
    #
    #     class TestTrait(Trait):
    #
    #         _sub_traits = TraitMapping()
    #         _sub_traits[TraitKey()]
    #
    #         @trait_property('float')
    #         def value(self):
    #             return 5.5
    #
    #         @trait_property('string')
    #         def extra(self):
    #             return "Extra info"
    #
    #     return TestTrait
    #




    def test_get_trait_properties(self):

        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        for prop in test_trait._trait_properties():
            assert isinstance(prop, TraitProperty)

        for value in test_trait.trait_property_values():
            assert not isinstance(value, TraitProperty)

    def test_trait_schema(self):
        """This test checks both versions of the schema."""
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

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

    def test_trait_schema_with_subtraits(self):

        test_trait = example_archive.SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

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

    def test_retrieve_sub_trait_by_dictionary(self):

        test_trait = example_archive.SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey('test_trait'),
                                                                  object_id='1')

        assert isinstance(test_trait['sub_trait'], Trait)

    def test_trait_descriptions(self):
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        assert hasattr(test_trait, 'get_pretty_name')
        assert hasattr(test_trait, 'get_documentation')
        assert hasattr(test_trait, 'get_description')

        assert test_trait.get_description() == "Description for SimpleTrait."

    def test_trait_documentation(self):
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        print(type(test_trait.get_documentation))
        print(test_trait.get_documentation())
        assert "Extended documentation" in test_trait.get_documentation()
        assert "Description for SimpleTrait" in test_trait.get_documentation()
        assert test_trait._documentation_format == 'markdown'

        assert "<strong>text</strong>" in test_trait.get_documentation('html')


    def test_trait_property_description(self):
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        assert test_trait.value.description == "TheValue"
        assert test_trait.extra.description == "ExtraInformation"

class TestTraitsInArchives:

    @pytest.fixture
    def example_archive(self):
        return example_archive.ExampleArchive()

    def test_trait_pretty_names(self, example_archive):
        # type: (example_archive.ExampleArchive) -> None
        image_trait_classes = example_archive.available_traits.get_traits(trait_type_filter='image')
        a_trait = image_trait_classes[0]
        assert issubclass(a_trait, Trait)
        assert a_trait.get_pretty_name() == 'Image'

    def test_trait_qualifer_pretty_name(self, example_archive):
        # type: (example_archive.ExampleArchive) -> None
        image_trait_classes = example_archive.available_traits.get_traits(trait_name_filter='image-red')
        a_trait = image_trait_classes[0]
        assert issubclass(a_trait, Trait)
        assert issubclass(a_trait, TraitDescriptionsMixin)
        assert a_trait.get_qualifier_pretty_name('red') == 'Red'

        # red_image_trait_key = example_archive.available_traits.update_key_with_defaults('image-red')
        image_trait = example_archive.get_full_sample()['Gal1']['image-red']
        assert isinstance(image_trait, Trait)
        assert isinstance(image_trait, TraitDescriptionsMixin)
        assert image_trait.get_qualifier_pretty_name('red') == 'Red'


class TestTraitKeys:


    @pytest.fixture
    def valid_traitkey_list(self):
        return [
            TraitKey('my_trait', 'qual', 'branch', 'ver'),
            TraitKey('my_trait', 'qual', 'branch', 'v0.3'),
            TraitKey('my_trait', 'qual', 'branch', '0.5'),
            TraitKey('my_trait', 'qual', 'branch', '135134'),
            TraitKey('my_trait', 'I', 'branch', 'ver'),
            TraitKey('my_trait', 'r', 'branch', 'ver'),
            TraitKey('my_trait', 'OII3727', 'branch', 'ver'),
            TraitKey('my_trait', '2', 'branch', 'ver'),
            TraitKey('my_trait', '2_', 'branch', 'ver'),
            TraitKey('my_trait', '65632.81', 'branch', 'ver')
        ]

    def test_traitkey_fully_qualified(self):

        # Check a selection of TraitKeys are valid (i.e. they don't raise an error)
        TraitKey('my_trait', 'qual', 'branch', 'ver')
        TraitKey('my_trait', 'qual', 'branch', 'v0.3')
        TraitKey('my_trait', 'qual', 'branch', '0.5')
        TraitKey('my_trait', 'qual', 'branch', '135134')
        TraitKey('my_trait', 'I', 'branch', 'ver')
        TraitKey('my_trait', 'r', 'branch', 'ver')
        TraitKey('my_trait', 'OII3727', 'branch', 'ver')
        TraitKey('my_trait', '2', 'branch', 'ver')
        TraitKey('my_trait', '2_', 'branch', 'ver')
        TraitKey('my_trait', '65632.81', 'branch', 'ver')

        # Check that invalid TraitKeys raise an error on construction
        invalid_trait_types = ("3band", "my-trait")
        for t in invalid_trait_types:
            with pytest.raises(ValueError):
                print(t)
                TraitKey(t, "v0.3")

        # Check that TraitKeys can be constructed from their strings
        TraitKey.as_traitkey("image-I:gama(v0.3)")

    def test_string_traitkeys_reconstruction(self, valid_traitkey_list):
        for tk in valid_traitkey_list:
            assert TraitKey.as_traitkey(str(tk)) == tk

    def test_traitkey_string_forms(self):

        test_list = [
            (TraitKey('my_trait'), 'my_trait'),
            (TraitKey('my_trait', trait_qualifier='qual'), 'my_trait-qual'),
            (TraitKey('my_trait', version='v2'), 'my_trait(v2)'),
            (TraitKey('my_trait', branch='b2'), 'my_trait:b2')
        ]

        for tk, string_representation in test_list:
            assert str(tk) == string_representation

    def test_traitkey_not_fully_qualified(self):
        TraitKey('my_trait')
        TraitKey('my_trait', 'qual')
        TraitKey('my_trait', branch='b1')
        TraitKey('my_trait', version='v1')


    def test_traitkey_trait_names_classmethod(self):
        # Class method approach
        assert TraitKey.as_trait_name('trait', 'qual') == 'trait-qual'

    # def test_traitkey_trait_names_instancemethod(self):
    #     # Instance method approach
    #     assert TraitKey('trait', 'qual').as_trait_name() == 'trait-qual'

    def test_convenience_trait_key_validation_functions(self):


        with pytest.raises(ValueError):
            validate_trait_name("blah:fsdf")

        with pytest.raises(ValueError):
            validate_trait_type("line_map-blue")

        validate_trait_name("line_map-blue")
        validate_trait_type("line_map")

class TestTraitRegistry:

    def test_trait_creation_with_inline_subtraits(self):

        class MyTrait(Trait):
            sub_traits = TraitRegistry()
            # Class defined inline:
            @sub_traits.register
            class MySubTrait(Trait):
                trait_type = 'sub_trait'
                @trait_property('string')
                def value(self):
                    return 'inline_sub_trait'

        # Check that the class remains after the registration.
        assert MyTrait.MySubTrait is not None
        assert issubclass(MyTrait.MySubTrait, Trait)

    def test_trait_creation_with_external_trait(self):

        class SubTraitClass(Trait):
            trait_type = 'sub_trait'
            @trait_property('string')
            def value(self):
                return 'external sub-trait'

        class MyTrait(Trait):
            sub_traits = TraitRegistry()
            sub_traits.register(SubTraitClass)

    def test_trait_registration(self):
        class MyTrait(Trait):
            trait_type = 'mytrait'
        tr = TraitRegistry()
        tr.register(MyTrait)
        assert tr.retrieve_with_key(TraitKey('mytrait')) is MyTrait

    def test_trait_names(self):
        class MyTrait(Trait):
            trait_type = 'mytrait'
        tr = TraitRegistry()
        tr.register(MyTrait)
        assert tr.retrieve_with_key(TraitKey('mytrait')) is MyTrait



    # def test_trait_registration_with_branches(self):
    #
    #     class MyTrait(Trait):
    #         available_versions = {'v1', 'v2'}
    #
    #     TraitRegistry().register(SubTraitClass)


