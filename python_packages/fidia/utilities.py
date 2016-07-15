from copy import deepcopy
from collections import Iterable, Sized

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

class SchemaDictionary(dict):
    """A dictionary class that can update with nested dicts, but does not allow changes.

    Note that this is not fully implemented. It only prevents changes introduced through the `.update` method. See ASVO-

    """
    def update(self, other_dict):

        if not hasattr(other_dict, 'keys'):
            raise TypeError("A SchemaDictionary can only be updated with a dict-like object.")
        for key in other_dict.keys():
            if key not in self:
                # New material. Add (a copy of) it. If it is a dictionary
                # but not a SchemaDictonary, make it a SchemaDictionary
                if isinstance(other_dict[key], dict) and not isinstance(other_dict[key], SchemaDictionary):
                    to_add = SchemaDictionary(other_dict[key])
                else:
                    to_add = deepcopy(other_dict[key])
                self[key] = to_add
            elif key in self and not isinstance(self[key], dict):
                # Key already exists and is not a dictionary, so check that the value has not changed.
                if self[key] != other_dict[key]:
                    raise ValueError("Invalid attempt to change value at key '%s' in update" % key)
            elif key in self and isinstance(self[key], dict) and isinstance(other_dict[key], dict):
                # Key already exists and is a dictionary, so recurse the update.
                self[key].update(other_dict[key])
            else:
                # Something's wrong, probably a type mis-match.
                raise Exception("The SchemaDictionary %s can not be updated with %s" % (self, other_dict[key]))

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
            return self._version_defaults[branch]

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


class Default: pass

def is_list_or_set(obj):
    """Return true if the object is a list, set, or other sized iterable (but not a string!)"""
    return isinstance(obj, Iterable) and isinstance(obj, Sized)