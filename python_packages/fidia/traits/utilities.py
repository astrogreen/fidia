from .. import slogging
log = slogging.getLogger(__name__)
log.enable_console_logging()
log.setLevel(slogging.INFO)

from abc import ABCMeta
import collections
import re

#TraitKey = collections.namedtuple('TraitKey', ['trait_type', 'trait_name', 'object_id'], verbose=True)

#from builtins import property as _property, tuple as _tuple
from operator import itemgetter as _itemgetter

from ..exceptions import *

from ..descriptions import Description, Documentation, PrettyName

TRAIT_TYPE_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*')
TRAIT_PART_RE = re.compile(r'[a-zA-Z0-9_][a-zA-Z0-9_.]*')

TRAIT_KEY_RE = re.compile(
    r"""(?P<trait_type>{TRAIT_TYPE_RE})
        (?:-(?P<trait_qualifier>{TRAIT_PART_RE}))?
        (?::(?P<branch>{TRAIT_TYPE_RE}))?
        (?:\((?P<version>{TRAIT_PART_RE})\))?""".format(
            TRAIT_TYPE_RE=TRAIT_TYPE_RE.pattern,
            TRAIT_PART_RE=TRAIT_PART_RE.pattern),
    re.VERBOSE
)

class TraitKey(tuple):
    """TraitKey(trait_type, trait_name, version, object_id)"""

    __slots__ = ()

    _fields = ('trait_type', 'trait_qualifier', 'version', 'branch')

    def __new__(_cls, trait_type, trait_qualifier=None, branch=None, version=None):
        """Create new instance of TraitKey(trait_type, trait_qualifier, branch, version)"""
        if TRAIT_TYPE_RE.fullmatch(trait_type) is None:
            raise ValueError("Trait type %s doesn't match the required format %s"
                             % (trait_type, TRAIT_TYPE_RE.pattern))
        for item in (trait_qualifier, branch, version):
            if item is not None and TRAIT_PART_RE.fullmatch(item) is None:
                raise ValueError("Trait part %s doesn't match the required format %s"
                                 % (item, TRAIT_PART_RE.pattern))
        return tuple.__new__(_cls, (trait_type, trait_qualifier, branch, version))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        """Make a new TraitKey object from a sequence or iterable"""
        result = new(cls, iterable)
        if len(result) not in (1, 2, 3, 4):
            raise TypeError('Expected 1-4 arguments, got %d' % len(result))
        return result

    @classmethod
    def as_traitkey(cls, key):
        """Return a TraitKey for the given input.

        Effectively this is just a smart "cast" from string or tuple.

        """
        if isinstance(key, TraitKey):
            return key
        if isinstance(key, tuple):
            return cls(*key)
        if isinstance(key, str):
            match = TRAIT_KEY_RE.fullmatch(key)
            if match:
                return cls(trait_type=match.group('trait_type'),
                    trait_qualifier=match.group('trait_qualifier'),
                    branch=match.group('branch'),
                    version=match.group('version'))
        raise KeyError("Cannot parse key '{}' into a TraitKey".format(key))


    def __repr__(self):
        """Return a nicely formatted representation string"""
        return 'TraitKey(trait_type=%r, trait_qualifier=%r, branch=%r, version=%r)' % self

    def _asdict(self):
        """Return a new OrderedDict which maps field names to their values"""
        return collections.OrderedDict(zip(self._fields, self))

    def replace(_self, **kwds):
        """Return a new TraitKey object replacing specified fields with new values"""
        result = _self._make(map(kwds.pop, ('trait_type', 'trait_qualifier', 'branch', 'version'), _self))
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

    def __str__(self):
        trait_string = self.trait_type
        if self.trait_qualifier:
            trait_string += "-" + self.trait_qualifier
        if self.branch:
            trait_string += ":" + self.branch
        if self.version:
            trait_string += "(" + self.version + ")"
        return trait_string

    trait_type = property(_itemgetter(0), doc='Trait type')

    trait_qualifier = property(_itemgetter(1), doc='Trait qualifier')

    branch = property(_itemgetter(2), doc='Branch')

    version = property(_itemgetter(3), doc='Version')

def parse_trait_key(key):
    """Return a fully fledged TraitKey for the key given.

    Effectively this is just a smart "cast" from string or tuple."""
    return TraitKey.as_traitkey(key)


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
            log.debug("TraitKey fully defined")
            return self._mapping[key]

        # CASES: Wild-card on one element
        elif key.replace(branch=None) in known_keys:
            log.debug("Wildcard on object_id")
            return self._mapping[key.replace(branch=None)]
        elif key.replace(version=None) in known_keys:
            log.debug("Wildcard on version")
            return self._mapping[key.replace(version=None)]
        elif key.replace(trait_qualifier=None) in known_keys:
            log.debug("Wildcard on trait_qualifier")
            return self._mapping[key.replace(trait_qualifier=None)]

        # CASES: Wild-card on two elements
        elif key.replace(trait_qualifier=None, branch=None) in known_keys:
            log.debug("Wildcard on both branch and trait_qualifier")
            return self._mapping[key.replace(trait_qualifier=None, branch=None)]
        elif key.replace(branch=None, version=None) in known_keys:
            log.debug("Wildcard on both branch and version")
            return self._mapping[key.replace(branch=None, version=None)]
        elif key.replace(trait_qualifier=None, version=None) in known_keys:
            log.debug("Wildcard on both trait_qualifier and version")
            return self._mapping[key.replace(trait_qualifier=None, version=None)]

        # CASE: Wild-card on three elements
        elif key.replace(trait_qualifier=None, version=None, branch=None) in known_keys:
            log.debug("Wildcard on trait_qualifier, and version, and branch")
            return self._mapping[key.replace(trait_qualifier=None, version=None, branch=None)]

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


class TraitProperty(metaclass=ABCMeta):

    allowed_types = [
        'string',
        'float',
        'int',
        'string.array',
        'float.array',
        'int.array'
    ]

    # pretty_name = PrettyName()
    # description = Description()
    # documentation = Documentation()

    pretty_name = None
    description = None
    documentation = None
    short_name = None

    def __init__(self, fload=None, fset=None, fdel=None, doc=None, type=None, name=None):
        self.fload = fload
        self.fset = fset
        self.fdel = fdel

        if name is None and fload is not None:
            name = fload.__name__
        self.name = name
        if doc is None and fload is not None:
            doc = fload.__doc__
        self.doc = doc

        # @TODO: Note that the type must be defined for now, should inherit from Trait parent class.
        self.type = type

    def loader(self, fload):
        """Decorator which sets the loader function for this TraitProperty"""
        if self.name is None:
            self.name = fload.__name__
        log.debug("Setting loader for TraitProperty '%s'", self.name)
        if self.doc is None:
            self.doc = fload.__doc__
        self.fload = fload
        return self

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._type = value

    @property
    def doc(self):
        return self.__doc__
    @doc.setter
    def doc(self, value):
        self.__doc__ = value

    def __get__(self, instance, instance_type):
        if instance is None:
            return self
        else:
            log.debug("Creating a bound trait property '%s.%s'", instance_type.__name__, self.name)
            return BoundTraitProperty(instance, self)


class BoundTraitProperty:

    def __init__(self, trait, trait_property):
        self._trait = trait
        self._trait_property = trait_property


    @property
    def name(self):
        return self._trait_property.name

    @property
    def type(self):
        return self._trait_property.type

    @property
    def doc(self):
        return self._trait_property.doc

    @property
    def short_name(self):
        return self._trait_property.short_name

    @property
    def description(self):
        return self._trait_property.description

    @property
    def documentation(self):
        return self._trait_property.documentation

    @property
    def pretty_name(self):
        return self._trait_property.pretty_name

    def __call__(self):
        """Retrieve the value of this TraitProperty"""
        return self.value

    @property
    def value(self):
        """The value of this TraitProperty, retrieved using cache requests.

        The value is retrieved from the cache stack of the archive to which this
        TraitProperty (and therefore Trait) belong to. At the bottom of the
        cache stack (i.e. if no cache has the necessary data), the request is
        passed back to the `uncached_value` property of this TraitProperty.
        """

        return self._trait.archive.cache.cache_request(self._trait, self.name)

    @property
    def uncached_value(self):
        """Retrieve the trait property value via the user provided loader.

        The preload and cleanup functions of the Trait are called if present
        before and after running the loader.

        """

        log.debug("Loading data for get for TraitProperty '%s'", self.name)

        try:

            # Preload the Trait if necessary.
            self._trait._load_incr()

            # Call the actual user defined loader function to get the value of the TraitProperty.
            value = self._trait_property.fload(self._trait)
        except DataNotAvailable:
            raise
        except Exception as e:
            log.exception("An exception occurred trying to retrieve the TraitProperty %s of Trait %s",
                          self._trait_property.name,
                          self._trait.trait_key
                          )
            raise DataNotAvailable("An error occurred trying to retrieve the requested data.")
        finally:
            # Cleanup the Trait if necessary.
            self._trait._load_decr()

        return value

# Register `BoundTraitProperty` as a subclass of `TraitProperty`. This makes
# `isinstance(value, TraitProperty)` work as expected for `TraitProperty`s that have
# been bound to their `Trait`.
TraitProperty.register(BoundTraitProperty)
