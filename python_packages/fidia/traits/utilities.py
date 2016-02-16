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

    def __contains__(self, item):
        try:
            self.__getitem__(item)
        except UnknownTrait:
            return False
        else:
            return True

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

    def get_traits_for_type(self, trait_type):
        """Return a list of all Trait classes mapped to a particular trait_type"""
        result = []
        for key in self._mapping:
            if key.trait_type == trait_type:
                result.append(self._mapping[key])
        return result

        # The same code written as a list comprehension
        #return [self._mapping[key] for key in self._mapping if key.trait_type == trait_type]

    def get_trait_types(self):
        """A list of the unique trait types in this TraitMapping."""
        return set([key.trait_type for key in self._mapping])

def trait_property(func_or_type):
    """Decorate a function which provides an individual property of a trait.

    This has an optional data-type designation. It can be used in one of two ways:

    @trait_property
    def value(self):
        return 5

    @trait_property('float')
    def value(self):
        return 5.5

    Implementation:

        Because the two examples actually look a bit different internally,
        this is implemented as a function that determines which case has been
        given. If the argument is callable, then it is assumed to be the first
        example, above, and if the argument is a string, then it is assumed to be
        the second example above.

    """""
    if isinstance(func_or_type, str):
        # Have been given a data type, so return a decorator:
        log.debug("Decorating trait_property with data-type %s", func_or_type)
        tp = TraitProperty(type=func_or_type)
        return tp.loader
    elif callable(func_or_type):
        # Have not been given a data type. Build the property directly:
        return TraitProperty(func_or_type)
    raise Exception("trait_property decorator used incorrectly. Check documentation.")

class TraitProperty(object):

    def __init__(self, fload=None, fget=None, fset=None, fdel=None, doc=None, type=None, name=None):
        self.fload = fload
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.name = name
        if doc is None and fload is not None:
            doc = fload.__doc__
        self.__doc__ = doc
        self.type = type

    def getter(self, fget):
        self.name = fget.__name__
        log.debug("Setting getter for TraitProperty '%s'", self.name)
        self.fget = fget
        return self

    def loader(self, fload):
        self.name = fload.__name__
        log.debug("Setting loader for TraitProperty '%s'", self.name)
        self.fload = fload
        return self

    def _get_with_load(self, obj):
        """Retrieve the trait property value via the user provided loader.

        The preload and cleanup functions of the Trait are called if present
        before and after running the loader.

        """

        log.debug("Loading data for get for TraitProperty '%s'", self.name)

        try:

            # Preload the Trait if necessary.
            obj._load_incr()

            # Call the actual user defined loader function to get the value of the TraitProperty.
            value = self.fload(obj)
        except DataNotAvailable:
            raise
        except:
            raise DataNotAvailable("An error occurred trying to retrieve the requested data.")
        finally:
            # Cleanup the Trait if necessary.
            obj._load_incr()

        return value

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            log.debug("Descriptor '%s.%s' retrieving its value...", type(obj).__name__, self.name)
            # No special getter (unusual) has been provided, so check for a
            # cached version, and either return that or run the loader to get
            # the value.

            # Check if obj has a trait_dict cache:
            try:
                log.debug("Checking for trait_dict cache...")
                obj._trait_dict
            except KeyError:
                # No trait cache: simply get value and return
                # @TODO: This case should really not be needed: all traits
                #        should eventually have a cache.
                log.debug("Object '%s' has no trait cache...using user provided loader.", obj)
                return self._get_with_load(obj)
            else:
                # Trait cache present, load value and store.
                if self.name not in obj._trait_dict:
                    log.debug("Object '%s' has not cached a value for '%s'.", obj, self.name)
                    # Data not yet cached
                    obj._trait_dict[self.name] = self._get_with_load(obj)
                else:
                    log.debug("Using cached a value for '%s' from object '%s'.", self.name, obj)
                return obj._trait_dict[self.name]

            raise Exception("Programming error")
