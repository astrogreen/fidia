from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from fidia.traits.abstract_base_traits import *
from fidia.traits.base_traits import Trait
from fidia.traits.utilities import TraitProperty, trait_property, TraitKey, TraitMapping
from fidia.archive import example_archive


def test_incomplete_trait_fails():

    class InvalidTestTrait(AbstractBaseTrait):

        @property
        def value(self):
            return 5

    with pytest.raises(TypeError):
        InvalidTestTrait()

    class ValidTestTrait(AbstractBaseTrait):

        @classmethod
        def all_keys_for_id(cls):
            return []

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


    def test_trait_keys(self):




        tk = TraitKey('my_trait', 'qual', 'branch', 'ver')

        assert TraitKey.as_traitkey(str(tk)) == tk

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
