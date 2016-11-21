"""
These tests check that the modules import, and that the namespace is populated
as expected.

"""
import logging

import pytest
from copy import deepcopy

from fidia.utilities import SchemaDictionary


def all_dicts_are_schema_dicts(schema_dict):
    for key in schema_dict:
        if isinstance(schema_dict[key], dict):
            if isinstance(schema_dict[key], SchemaDictionary):
                all_dicts_are_schema_dicts(schema_dict[key])
            else:
                return False
    return True

class TestSchemaDict:

    @pytest.fixture
    def example_schema_dict(self):
        return SchemaDictionary(
            a=1,
            b=2,
            subdict=SchemaDictionary(
                sa=1,
                sb=2),
            subsub=SchemaDictionary(
                sa=1,
                sub=SchemaDictionary(
                    ssa=1,
                    ssb=2)
            )
        )

    def test_update_extend(self, example_schema_dict):
        """Extend the dict with a valid extension"""
        mine = SchemaDictionary(example_schema_dict)

        mine.update({'c': 3, 'subdict': {'sc': 3, 'sd': 4}})

        assert mine['c'] == 3
        assert mine['subdict']['sc'] == 3

    def test_update_change_value(self, example_schema_dict):
        mine = SchemaDictionary(example_schema_dict)

        with pytest.raises(ValueError):
            mine.update({'a': 10})
            print(mine)


    def test_update_change_sub_value(self, example_schema_dict):
        mine = SchemaDictionary(example_schema_dict)

        with pytest.raises(ValueError):
            mine.update({'subdict': {'sa': 10}})
            print(mine)

    def test_all_sub_dicts_same_type(self, example_schema_dict):
        mine = SchemaDictionary(example_schema_dict)

        assert all_dicts_are_schema_dicts(mine)

    def test_updating_keeps_schema_dicts(self, example_schema_dict):
        mine = SchemaDictionary(example_schema_dict)

        mine.update({'c': 3, 'subdict': {'sc': 3, 'sd': 4}})
        assert all_dicts_are_schema_dicts(mine)

        mine.update({'c': 3, 'newsubdict': {'sc': 3, 'sd': 4}})
        assert all_dicts_are_schema_dicts(mine)

        mine.update({'c': 3, 'newdeepdict': {'sc': 3, 'sd': {"another": 3}}})
        assert all_dicts_are_schema_dicts(mine)

    def test_creation_with_subdicts_all_are_schema_dicts(self):

        test = SchemaDictionary(
            a=1,
            b=2,
            subdict={"sa": 1, "sb":2},
            subsub={"sa": 1, "sub": {"ssa": 1, "ssb":2}}
        )
        assert all_dicts_are_schema_dicts(test)

class FidiaGeneralTest:

    def check_sample_imports(self):
        from fidia import Sample

    # def test_logging_debug_turned_off(self):
    # 	import fidia
     #    import fidia.archive
     #    import fidia.sample
     #    import fidia.traits.base_traits
     #    import fidia.traits.utilities
     #    import fidia.traits.galaxy_traits
     #    import fidia.traits.generic_traits
     #    import fidia.traits.stellar_traits
    #
     #    log = logging.getLogger('fidia')
     #    for child_logger in log.
