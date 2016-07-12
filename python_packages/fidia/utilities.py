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
    """A dictionary class that can update with nested dicts."""
    def update(self, other_dict):
        if not hasattr(other_dict, 'keys'):
            raise TypeError("A SchemaDictionary can only be updated with a dict-like object.")
        for key in other_dict.keys():
            if key not in self:
                # New material. Add (a copy of) it.
                self[key] = deepcopy(other_dict[key])
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

def is_list_or_set(obj):
    """Return true if the object is a list, set, or other sized iterable (but not a string!)"""
    return isinstance(obj, Iterable) and isinstance(obj, Sized)