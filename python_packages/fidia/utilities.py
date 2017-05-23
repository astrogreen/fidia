from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List

# Python Standard Library Imports
import operator
from copy import deepcopy
import re
from collections import Iterable, Sized, MutableMapping
from contextlib import contextmanager
import os
import errno
import fcntl
import functools
from time import sleep

# Other Library Imports
from six.moves import reduce
from sortedcontainers import SortedDict

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

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