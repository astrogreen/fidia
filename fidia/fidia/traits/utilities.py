from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)

log.enable_console_logging()


import collections

#TraitKey = collections.namedtuple('TraitKey', ['trait_type', 'trait_name', 'object_id'], verbose=True)

#from builtins import property as _property, tuple as _tuple
from operator import itemgetter as _itemgetter

from ..exceptions import *

class TraitKey(tuple):
    """TraitKey(trait_type, trait_name, version, object_id)"""

    __slots__ = ()

    _fields = ('trait_type', 'trait_name', 'version', 'object_id')

    def __new__(_cls, trait_type, trait_name=None, version=None, object_id=None):
        """Create new instance of TraitKey(trait_type, trait_name, version, object_id)"""
        return tuple.__new__(_cls, (trait_type, trait_name, version, object_id))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        """Make a new TraitKey object from a sequence or iterable"""
        result = new(cls, iterable)
        if len(result) not in (1, 2, 3, 4):
            raise TypeError('Expected 1-4 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        """Return a nicely formatted representation string"""
        return 'TraitKey(trait_type=%r, trait_name=%r, version=%r, object_id=%r)' % self

    def _asdict(self):
        """Return a new OrderedDict which maps field names to their values"""
        return collections.OrderedDict(zip(self._fields, self))

    def replace(_self, **kwds):
        """Return a new TraitKey object replacing specified fields with new values"""
        result = _self._make(map(kwds.pop, ('trait_type', 'trait_name', 'version', 'object_id'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        """Return self as a plain tuple.  Used by copy and pickle."""
        return tuple(self)

    __dict__ = property(_asdict)

    def __getstate__(self):
        """Exclude the OrderedDict from pickling"""
        pass

    trait_type = property(_itemgetter(0), doc='Alias for field number 0')

    trait_name = property(_itemgetter(1), doc='Alias for field number 1')

    version = property(_itemgetter(2), doc='Alias for field number 2')

    object_id = property(_itemgetter(3), doc='Alias for field number 3')




class TraitMapping(collections.MutableMapping):

    # Functions to create dictionary like behaviour

    def __init__(self):
        self._mapping = dict()

    def __getitem__(self, key):
        """Function called on dict type read access"""
        if not isinstance(key, TraitKey):
            key = TraitKey(key)

        known_keys = self._mapping.keys()

        # CASE: Key fully defined
        if key in known_keys:
            return self._mapping[key]

        # CASES: Wild-card on one element
        elif key.replace(object_id=None) in known_keys:
            # Wildcard on object_id
            return self._mapping[key.replace(object_id=None)]
        elif key.replace(version=None) in known_keys:
            # Wildcard on version
            return self._mapping[key.replace(version=None)]
        elif key.replace(trait_name=None) in known_keys:
            # Wildcard on trait_name
            return self._mapping[key.replace(trait_name=None)]

        # CASES: Wild-card on two elements
        elif key.replace(trait_name=None, object_id=None) in known_keys:
            # Wildcard on both object_id and trait_name
            return self._mapping[key.replace(trait_name=None, object_id=None)]
        elif key.replace(object_id=None, version=None) in known_keys:
            # Wildcard on both object_id and version
            return self._mapping[key.replace(object_id=None, version=None)]
        elif key.replace(trait_name=None, version=None) in known_keys:
            # Wildcard on both trait_name and version
            return self._mapping[key.replace(trait_name=None, version=None)]

        # CASE: Wild-card on three elements
        elif key.replace(trait_name=None, version=None, object_id=None) in known_keys:
            # Wildcard on trait_name, and version, and object_id
            return self._mapping[key.replace(trait_name=None, version=None, object_id=None)]

        else:
            # No suitable data loader found
            raise UnknownTrait("No known way to load trait for key {}".format(key))

    def __setitem__(self, key, value):
        if not isinstance(key, TraitKey):
            key = TraitKey(key)
        self._mapping[key] = value

    def __delitem__(self, key):
        if not isinstance(key, TraitKey):
            key = TraitKey(key)
        del self._mapping[key]

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)


class trait_property(object):

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        self.type = type

    def __call__(self, type=None):
        self.type = type
        return self

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)
