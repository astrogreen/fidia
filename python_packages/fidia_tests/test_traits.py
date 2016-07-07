from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from fidia.traits.abstract_base_traits import *
from fidia.traits.base_traits import Trait
from fidia.traits import TraitProperty, trait_property, TraitKey, TraitRegistry
from fidia.archive import example_archive


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

        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        schema = test_trait.schema()

        assert isinstance(schema, dict)

        assert 'value' in schema
        assert schema['value'] == 'float'
        assert 'extra' in schema
        assert schema['extra'] == 'string'

    def test_trait_schema_with_subtraits(self):

        test_trait = example_archive.SimpleTraitWithSubtraits(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        schema = test_trait.schema()

        assert isinstance(schema, dict)

        assert 'value' in schema
        assert schema['value'] == 'float'
        assert 'extra' in schema
        assert schema['extra'] == 'string'

        # Hierarchical part of schema:
        assert 'sub_trait' in schema
        assert isinstance(schema['sub_trait'], dict)
        assert 'value' in schema['sub_trait']


    def test_trait_descriptions(self):
        test_trait = example_archive.SimpleTrait(example_archive.Archive(), TraitKey('test_trait'), object_id='1')

        assert hasattr(test_trait, 'pretty_name')
        assert hasattr(test_trait, 'documentation')
        assert hasattr(test_trait, 'description')

        assert test_trait.description == "Description for SimpleTrait."

        print(type(test_trait.documentation))
        print(test_trait.documentation)
        assert "Extended documentation" in test_trait.documentation
        assert "Description for SimpleTrait" in test_trait.documentation


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


