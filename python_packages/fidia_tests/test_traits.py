from __future__ import absolute_import, division, print_function, unicode_literals


import pytest

from fidia.traits.abstract_base_traits import *

def test_incomplete_trait_fails():

    class InvalidTestTrait(AbstractBaseTrait):

        @property
        def value(self):
            return 5

    with pytest.raises(TypeError):
        InvalidTestTrait()

    class ValidTestTrait(AbstractBaseTrait):

        def known_keys(cls, object_id):
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