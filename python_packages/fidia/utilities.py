from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List

# Python Standard Library Imports
import operator
from copy import deepcopy
import re
from collections import Iterable, Sized, MutableMapping
from contextlib import contextmanager
from inspect import isclass, getattr_static
import os
import errno
import fcntl
import functools
from time import sleep

# Other Library Imports
from six.moves import reduce, zip
from sortedcontainers import SortedDict
from sqlalchemy.ext.orderinglist import OrderingList
import sqlalchemy.orm.collections as sa_collections


# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = [
    'none_at_indices', 'camel_case', 'fidia_classname', 'snake_case', 'is_list_or_set',
    'WildcardDictionary', 'SchemaDictionary', 'MultiDexDict', 'DefaultsRegistry',
    'Inherit', 'Default',
    'RegexpGroup', 'exclusive_file_lock', 'classorinstancemethod', 'reset_cached_property'
]

def reset_cached_property(object, property_name):
    """Checks if a cached_property has been cached, and if so, resets it.

    UNTESTED!!!

    """
    # @TODO: Write some unit tests for this!
    if getattr(type(object), property_name) is not getattr_static(object, property_name):
        # The instance has something other than the descriptor at the
        delattr(object, property_name)

def none_at_indices(tup, indices):
    result = tuple()
    for index in range(len(tup)):
        if index in indices:
            result += (None,)
        else:
            result += (tup[index],)
    return result

class WildcardDictionary(dict):
    def get_all(self, wildkey):
        """Return a list of all matching members."""
        start = 0
        wildcard_indices = set()
        for i in range(wildkey.count(None)):
            index = wildkey.index(None, start)
            wildcard_indices.add(index)
            start = index + 1

        result = dict()
        for key in self:
            if none_at_indices(key, wildcard_indices) == wildkey:
                result[key] = self[key]

        return result

class SchemaDictionary(SortedDict):
    """A dictionary class that can update with nested dicts, but does not allow changes.

    Note that this is not fully implemented. It only prevents changes introduced through the `.update` method. See ASVO-

    """

    @classmethod
    def _convert_to_schema_dictionary(cls, dictionary):
        if isinstance(dictionary, dict) and not isinstance(dictionary, SchemaDictionary):
            dictionary = SchemaDictionary(dictionary)
        for key in dictionary:
            if isinstance(dictionary[key], dict):
                dictionary[key] = cls._convert_to_schema_dictionary(dictionary[key])
        return dictionary

    def __init__(self, *args, **kwargs):
        super(SchemaDictionary, self).__init__(str, *args, **kwargs)

        self.make_sub_dicts_schema_dicts()

    def make_sub_dicts_schema_dicts(self):
        # Walk the new dictionary, replacing any plain dicts with SchemaDicts:
        for key in self:
            if isinstance(self[key], dict):
                self[key] = self._convert_to_schema_dictionary(self[key])


    def update(self, other_dict, set_updates_allowed=True):

        if not hasattr(other_dict, 'keys'):
            raise TypeError("A SchemaDictionary can only be updated with a dict-like object.")
        for key in other_dict.keys():
            if key not in self:
                # New material. Add (a copy of) it. If it is a dictionary, make
                # a copy as a SchemaDictionary
                if isinstance(other_dict[key], dict):
                    to_add = SchemaDictionary(other_dict[key])
                else:
                    to_add = deepcopy(other_dict[key])
                self[key] = to_add
            elif key in self and not isinstance(self[key], SchemaDictionary):
                # Key already exists so see if we can either check it does not change or update it
                if set_updates_allowed and hasattr(self[key], 'update'):
                    self[key].update(other_dict[key])
                else:
                    if self[key] != other_dict[key]:
                        raise ValueError("Invalid attempt to change value at key '%s' in update from '%s' to '%s'" %
                                         (key, self[key], other_dict[key]))
            elif key in self and isinstance(self[key], dict) and isinstance(other_dict[key], dict):
                # Key already exists and is a dictionary, so recurse the update.
                self[key].update(other_dict[key])
            else:
                # Something's wrong, probably a type mis-match.
                raise Exception("The SchemaDictionary %s can not be updated with %s" % (self, other_dict[key]))

    def delete_empty(self):
        """Remove any empty dictionaries in this and nested dictionaries."""

        self.make_sub_dicts_schema_dicts()

        to_delete = set()

        for key in self.keys():
            if isinstance(self[key], SchemaDictionary):
                if len(self[key].keys()) == 0:
                    to_delete.add(key)
                else:
                    self[key].delete_empty()
                    # Check if the previously un-empty dictionary is now truly empty.
                    if len(self[key].keys()) == 0:
                        to_delete.add(key)

        for key in to_delete:
            del self[key]


class MultiDexDict(MutableMapping):

    __slots__ = ['_internal_dict', 'index_cardinality']

    def __init__(self, index_cardinality):
        super(MultiDexDict, self).__init__()
        self.index_cardinality = index_cardinality
        self._internal_dict = dict()  # type: MultiDexDict

    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            key = (key, )
        if len(key) != self.index_cardinality:
            raise KeyError("Key has wrong cardinality.")
        if len(key) == 1:
            # Base cases
            # log.debug("Setting base case for key %s", key)
            self._internal_dict[key[0]] = value
            # log.debug("Updated internal state: %s", self._internal_dict)
        else:
            # Recursive case
            # log.debug("Recursively setting for key %s", key)
            if key[0] not in self._internal_dict:
                # log.debug("Creating new subdict for key: %s", key)
                self._internal_dict[key[0]] = MultiDexDict(self.index_cardinality - 1)
            self._internal_dict[key[0]][key[1:]] = value
            # log.debug("Updated internal state: %s", self._internal_dict)

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            key = (key, )
        if len(key) > self.index_cardinality:
            raise KeyError("Key has two many indicies!")
        if len(key) == 1:
            # Base case
            return self._internal_dict[key[0]]
        elif len(key) <= self.index_cardinality:
            # Recursive case
            return self._internal_dict[key[0]][key[1:]]

    def __delitem__(self, key):
        if not isinstance(key, tuple):
            key = (key, )
        if len(key) > self.index_cardinality:
            raise KeyError("Key has two many indicies!")
        if len(key) == 1:
            # Base case
            del self._internal_dict[key[0]]
        elif len(key) <= self.index_cardinality:
            # Recursive case
            del self._internal_dict[key[0]][key[1:]]

    def __iter__(self):
        return iter(self._internal_dict)

    def keys(self, depth=0):

        if depth == 0:
            depth = self.index_cardinality
        if depth == 1:
            return self._internal_dict.keys()
        if depth > 1:
            res = []
            for key in self._internal_dict.keys():
                for sub_key in self._internal_dict[key].keys(depth=depth-1):
                    if isinstance(sub_key, tuple):
                        res.append((key,) + sub_key)
                    else:
                        res.append((key,) + (sub_key,))
            return res

    def __eq__(self, other):
        if isinstance(other, MultiDexDict):
            return self.as_nested_dict() == other.as_nested_dict()
        else:
            return self.as_nested_dict() == other

    def __contains__(self, item):
        if not isinstance(item, tuple):
            return item in list(self.keys(1))
        else:
            return item in self.keys(len(item))

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        return repr(self.as_nested_dict())

    def update(self, other):
        # if isinstance(other, MultiDexDict):
        if isinstance(other, MultiDexDict) and self.index_cardinality != other.index_cardinality:
            raise ValueError("Cannot combine MultiDexDicts of different index cardinality")
        for key in other.keys():
            self[key] = other[key]


    def as_nested_dict(self):
        if self.index_cardinality == 1:
            return self._internal_dict
        else:
            result = dict()
            for key in self._internal_dict:
                result[key] = self._internal_dict[key].as_nested_dict()
            return result

class Inherit: pass

class DefaultsRegistry:

    def __init__(self, default_branch=None, version_defaults={}):
        self._default_branch = default_branch
        self._version_defaults = SchemaDictionary(version_defaults)

    @property
    def branch(self):
        """
        Return the default branch.

        If the default has not been set, then return `Inherit`

        """
        # if self._default_branch is None:
        #     return Inherit
        # else:
        return self._default_branch

    def version(self, branch):
        """Return the default version for the given branch.

        If the dictionary has not been initialised, then return `Inherit`.

        """
        # if self._version_defaults == {}:
        #     return Inherit
        if branch is None:
            return None
        else:
            try:
                return self._version_defaults[branch]
            except KeyError:
                raise KeyError("%s has no default for branch '%s'" % (self, branch))

    def set_default_branch(self, branch, override=False):
        # type: (str, bool) -> None
        if branch is None:
            return
        if override or self._default_branch is None:
            self._default_branch = branch
        else:
            # Trying to update the default which has already been set.
            # Throw an error only if this attempt would actually change
            # the default.
            if self._default_branch != branch:
                raise ValueError("Attempt to change the default branch.")

    def set_default_version(self, branch, version, override=False):
        # type: (str, str, bool) -> None
        if branch not in self._version_defaults or override:
            self._version_defaults[branch] = version
        elif self._version_defaults[branch] != version:
            raise ValueError("Attempt to change the default version for branch '%s' from '%s'"
                             % (branch, self._version_defaults[branch]))

    def update_defaults(self, other_defaults, override=False):
        # type: (DefaultsRegistry, bool) -> None
        self.set_default_branch(other_defaults._default_branch, override=override)
        self._version_defaults.update(other_defaults._version_defaults)

    def __str__(self):
        return "DefaultsRegistry(default_branch=%s, version_defaults=%s" % (
            self._default_branch, self._version_defaults
        )

class Default: pass

def camel_case(snake_case_string):
    # type: (str) -> str
    """Convert a string from snake_case to CamelCase.

    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case

    """
    if not isinstance(snake_case_string, str):
        raise ValueError("snake_case() works only on strings")
    return ''.join(word.capitalize() or '_' for word in snake_case_string.split('_'))

def snake_case(camel_case_string):
    # type (str) -> str
    """Convert a string from CamelCase to snake_case."""
    if not isinstance(camel_case_string, str):
        raise ValueError("camel_case() works only on strings")
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case_string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def is_list_or_set(obj):
    """Return true if the object is a list, set, or other sized iterable (but not a string!)"""
    return isinstance(obj, Iterable) and isinstance(obj, Sized) and not isinstance(obj, str) and not isinstance(obj, bytes)

def fidia_classname(obj, check_fidia=False):
    """Determine the name of the class for the given object in the context of FIDIA.
    
    This basically just returns the name of the class for the given object. Object can be a class or instance.
    
    If the object is not from FIDIA itself, it will return the full module path to the object, e.g.:
    
        >>> import collections
        >>> fidia_classname(collections.OrderedDict)
        collections.OrderedDict
        >>> import fidia.utilities
        >>> fidia_classname(fidia.utilities.SchemaDictionary)
        SchemaDictionary

    """
    if isclass(obj):
        klass = obj
    else:
        klass = obj.__class__

    if klass.__module__.startswith("fidia."):
        is_fidia = True
        name = ""
    else:
        is_fidia = False
        name = klass.__module__ + "."

    name += klass.__name__

    if check_fidia:
        return name, is_fidia
    else:
        return name

class exclusive_file_lock:
    """A context manager which will block while another process holds a lock on the named file.

    While another process is executing this context, this process will block,
    and only start executing the context once the lock has been released.

    Adapted from http://stackoverflow.com/questions/30407352/how-to-prevent-a-race-condition-when-multiple-processes-attempt-to-write-to-and

    """

    def __init__(self, filename):
        self.lockfilename = filename + '.LOCK'

    def __enter__(self):

        # Loop until a lock file can be created:
        lock_aquired = False
        n_waits = 0
        while not lock_aquired:
            try:
                fd = os.open(self.lockfilename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                fcntl.lockf(fd, fcntl.LOCK_EX)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                else:
                    # Wait some time for the lock to be cleared before trying again.
                    sleep(0.5)
                    n_waits += 1
                    if n_waits == 10:
                        log.warning("Waiting for exclusive lock on file '%s'", self.lockfilename)
                    if n_waits == 10:
                        log.warning("Still waiting for exclusive lock on file '%s': stale lockfile?",
                                    self.lockfilename)

            except:
                raise
            else:
                lock_aquired = True

        # Lock has been aquired. Open the file
        self.f = os.fdopen(fd)

        return

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context complete. Release the lock.
        os.remove(self.lockfilename)
        self.f.close()


class classorinstancemethod(object):
    """Define a method which will work as both a class or an instance method.

    See: http://stackoverflow.com/questions/2589690/creating-a-method-that-is-simultaneously-an-instance-and-class-method

    """
    def __init__(self, method):
        self.method = method

    def __get__(self, obj=None, objtype=None):
        @functools.wraps(self.method)
        def _wrapper(*args, **kwargs):
            if obj is not None:
                return self.method(obj, *args, **kwargs)
            else:
                return self.method(objtype, *args, **kwargs)
        return _wrapper

class RegexpGroup:
    def __init__(self, *args):
        self.regexes = []
        self.plain_items = []
        for item in args:
            # Add all non-regex items to one list
            if hasattr(item, 'match'):
                self.regexes.append(item)
            else:
                self.plain_items.append(item)

    def __contains__(self, item):
        # First check plain list:
        if item in self.plain_items:
            return True
        else:
            for regex in self.regexes:
                if regex.match(item):
                    return True
        return False

def ordering_list_dict(ordering_attr, mapping_attribute):
    """Factory to create an ordered dictionary-like relationship for a :func:`.relationship`."""
    return lambda: OrderingListDict(ordering_attr, mapping_attribute)

class OrderingListDict(list):
    """A custom list that manages position information for its children.

    The :class:`.OrderingListDict` object is normally set up using the
    :func:`.ordering_list` factory function, used in conjunction with
    the :func:`.relationship` function.

    """

    __emulates__ = list

    def __init__(self, ordering_attr=None, mapping_attribute=None,
    reorder_on_append=False):
        """A custom list that manages position information for its children, and
        also provides dictionary like access on a specified child attribute.

        This is based on the SQLAlchemy extension `OrderingList`, and the
        documentation there should be read.

        This implementation relies on the list starting in the proper order,
        so be **sure** to put an ``order_by`` on your relationship.

        :param ordering_attr:
          Name of the attribute that stores the object's order in the
          relationship.

        :param mapping_attribute:
          Name of the child attribute to use as the key for dictionary-like
          access.

        :param ordering_func: Optional.  A function that maps the position in
          the Python list to a value to store in the
          ``ordering_attr``.  Values returned are usually (but need not be!)
          integers.

          An ``ordering_func`` is called with two positional parameters: the
          index of the element in the list, and the list itself.

          If omitted, Python list indexes are used for the attribute values.
          Two basic pre-built numbering functions are provided in this module:
          ``count_from_0`` and ``count_from_1``.  For more exotic examples
          like stepped numbering, alphabetical and Fibonacci numbering, see
          the unit tests.

        :param reorder_on_append:
          Default False.  When appending an object with an existing (non-None)
          ordering value, that value will be left untouched unless
          ``reorder_on_append`` is true.  This is an optimization to avoid a
          variety of dangerous unexpected database writes.

          SQLAlchemy will add instances to the list via append() when your
          object loads.  If for some reason the result set from the database
          skips a step in the ordering (say, row '1' is missing but you get
          '2', '3', and '4'), reorder_on_append=True would immediately
          renumber the items to '1', '2', '3'.  If you have multiple sessions
          making changes, any of whom happen to load this collection even in
          passing, all of the sessions would try to "clean up" the numbering
          in their commits, possibly causing all but one to fail with a
          concurrent modification error.

          Recommend leaving this with the default of False, and just call
          ``reorder()`` if you're doing ``append()`` operations with
          previously ordered instances or when doing some housekeeping after
          manual sql operations.

        """
        self.ordering_attr = ordering_attr
        self.reorder_on_append = reorder_on_append

        self._mapping = dict()
        self._mapping_attribute = mapping_attribute



    def _add_mapping(self, item):
        """Add an item to the mapping cache."""
        try:
            key = getattr(item, self._mapping_attribute)
        except KeyError:
            log.warn("Item '%s' does not provide the mapping attribute '%s'", item, self._mapping_attribute)
            return
        else:
            if key in self._mapping and self._mapping[key] is not item:
                log.error("Item '%s' added has same key as existing item '%s'", item, self._mapping[key])
                # To raise an exception here, the state must be correctly
                # cleaned up in higher level functions. So for now we just print
                # an error and continue. This will make the mapping access
                # problematic, but keeps state consistent.

            self._mapping[key] = item

    def _remove_mapping(self, item):
        """Remove an item from the mapping cache."""
        try:
            key = getattr(item, self._mapping_attribute)
        except KeyError:
            pass
        else:
            del self._mapping[key]

    def _get_order_value(self, entity):
        return getattr(entity, self.ordering_attr)

    def _set_order_value(self, entity, value):
        setattr(entity, self.ordering_attr, value)



    def reorder(self):
        """Synchronize ordering for the entire collection.

        Sweeps through the list and ensures that each object has accurate
        ordering information set.

        Also checks and updates the dictionary-like access cache.

        """
        for index, entity in enumerate(self):
            self._order_entity(index, entity, True)

        self._mapping = dict()
        for item in self:
            self._add_mapping(item)

    # As of 0.5, _reorder is no longer semi-private
    _reorder = reorder

    def _order_entity(self, index, entity, reorder=True):
        have = self._get_order_value(entity)

        # Don't disturb existing ordering if reorder is False
        if have is not None and not reorder:
            return

        # should_be = self.ordering_func(index, self)
        should_be = index
        if have != should_be:
            self._set_order_value(entity, should_be)


    def append(self, entity):
        super(OrderingListDict, self).append(entity)
        self._order_entity(len(self) - 1, entity, self.reorder_on_append)
        self._add_mapping(entity)

    def _raw_append(self, entity):
        """Append without any ordering behavior."""

        super(OrderingList, self).append(entity)
    _raw_append = sa_collections.collection.adds(1)(_raw_append)

    def insert(self, index, entity):
        super(OrderingList, self).insert(index, entity)
        self._reorder()

    def remove(self, entity):

        super(OrderingListDict, self).remove(entity)

        adapter = sa_collections.collection_adapter(self)
        if adapter and adapter._referenced_by_owner:
            self._reorder()
        self._remove_mapping(entity)

    def pop(self, index=-1):
        entity = super(OrderingList, self).pop(index)
        self._reorder()
        return entity

    def __getitem__(self, item):
        if not isinstance(item, int):
            if item in self._mapping:
                return self._mapping[item]
            else:
                log.debug("Key '%s' not found. Availblae keys: %s", item, list(self._mapping.keys()))

                # We have most likely reached this point when the instrumented
                # list `setitem` at sqlaclchemy.orm.collections is called. When
                # setitem is called on a list, e.g.:
                #
                # >>> mylist[3] = 'item'
                #
                # the indexed item already exists, and we are asking for it to
                # be replaced with the new item. SQLAlchemy expects this, and so
                # it must get the existing item and delete it. However, if we
                # are accessing the list as a dictionary, then this item won't
                # exist. We return `None` here so that alchemy skips it's delete
                # step.
                return None
        return super(OrderingListDict, self).__getitem__(item)

    def __setitem__(self, index, entity):
        if isinstance(index, slice):
            step = index.step or 1
            start = index.start or 0
            if start < 0:
                start += len(self)
            stop = index.stop or len(self)
            if stop < 0:
                stop += len(self)

            for i in range(start, stop, step):
                self.__setitem__(i, entity[i])
        else:
            if not isinstance(index, int):
                self.append(entity)
                return
            self._add_mapping(entity)
            self._order_entity(index, entity, True)
            super(OrderingListDict, self).__setitem__(index, entity)

    def __delitem__(self, index):
        super(OrderingListDict, self).__delitem__(index)
        self._remove_mapping(self[index])
        self._reorder()

    def __setslice__(self, start, end, values):
        super(OrderingList, self).__setslice__(start, end, values)
        self._reorder()

    def __delslice__(self, start, end):
        super(OrderingList, self).__delslice__(start, end)
        self._reorder()

    def keys(self):
        return self._mapping.keys()

    def values(self):
        return self
    
    def __contains__(self, item):
        # First check as though dictionary-like:
        if item in self._mapping:
            return True
        # Second check normal contains
        return super(OrderingListDict, self).__contains__(item)
