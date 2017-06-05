"""
These tests check that the modules import, and that the namespace is populated
as expected.

"""
import logging

import pytest
from copy import deepcopy

from fidia.utilities import *


class TestFidiaImportsAndPackageLayout:

    def test_fidia_import(self):
        import fidia

    def test_submodule_import(self):
        import fidia.archive
        import fidia.sample
        import fidia.column
        import fidia.astro_object
        import fidia.traits

    def test_toplevel_layout(self):
        import fidia
        print(dir(fidia))

        assert 'Archive' in dir(fidia)
        assert 'Sample' in dir(fidia)
        assert 'Trait' in dir(fidia)
        # assert 'TraitCollection' in dir(fidia)

    def test_archive_pkg_layout(self):
        import fidia.archive
        print(dir(fidia.archive))
        assert 'Archive' in dir(fidia.archive)



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



def all_dicts_are_schema_dicts(schema_dict):
    from fidia.utilities import SchemaDictionary
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

class TestMultidexDict:

    @pytest.fixture
    def mdict(self):
        mdict = MultiDexDict(2)

        mdict['a', 'a'] = 1
        mdict['a', 'b'] = 2
        mdict['a', 'c'] = 3
        mdict['b', 'a'] = 4
        mdict['b', 'c'] = 5

        return mdict

    def test_creation_and_retrieval_full_key(self, mdict):

        assert mdict.as_nested_dict() == {
            'a': {'a': 1, 'b': 2, 'c':3},
            'b': {'a': 4, 'c': 5}
        }

        print(mdict['a', 'b'])

        assert mdict['a', 'a'] == 1
        assert mdict['a', 'b'] == 2
        assert mdict['a', 'c'] == 3
        assert mdict['b', 'a'] == 4
        assert mdict['b', 'c'] == 5

    def test_retrieval_incomplete_key(self, mdict):

        print(mdict.as_nested_dict())

        print(repr(mdict['a']))

        assert mdict['a'] == {'a': 1, 'b': 2, 'c':3}
        assert mdict['b'] == {'a': 4, 'c': 5}

    def test_keys(self, mdict):

        print(list(mdict.keys(1)))

        print(list(mdict.keys()))

        assert set(mdict.keys()) == {
            ('a', 'a'),
            ('a', 'b'),
            ('a', 'c'),
            ('b', 'a'),
            ('b', 'c')
        }

    def test_length(self, mdict):
        assert len(mdict) == 5

    def test_update(self, mdict):
        otherdict = MultiDexDict(2)
        otherdict['a', 'a'] = 11
        otherdict['a', 'd'] = 12
        otherdict['e', 'a'] = 13

        mdict.update(otherdict)

        assert mdict['a', 'a'] == 11
        assert mdict['a', 'd'] == 12
        assert mdict['e', 'a'] == 13

    def test_contains(self, mdict):

        assert 'a' in mdict
        assert 'b' in mdict
        assert ('a', 'a') in mdict


    def test_invalid_keys(self, mdict):

        with pytest.raises(KeyError):
            mdict['a', 'b', 'c']

        with pytest.raises(KeyError):
            mdict['not present', 'b']

    def test_delete(self):
        mdict = MultiDexDict(2)

        mdict['a', 'a'] = 1
        mdict['a', 'b'] = 2
        mdict['a', 'c'] = 3
        mdict['b', 'a'] = 4
        mdict['b', 'c'] = 5

        assert mdict['a', 'a'] == 1
        del mdict['a', 'a']
        with pytest.raises(KeyError):
            mdict['a', 'a']
        assert mdict.as_nested_dict() == {
            'a': {'b': 2, 'c': 3},
            'b': {'a': 4, 'c': 5}
        }

        del mdict['b']
        assert mdict.as_nested_dict() == {
            'a': {'b': 2, 'c': 3}
        }
