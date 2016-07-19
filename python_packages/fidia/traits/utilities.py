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
from ..utilities import is_list_or_set

TRAIT_TYPE_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*')
TRAIT_PART_RE = re.compile(r'[a-zA-Z0-9_][a-zA-Z0-9_.]*')

TRAIT_NAME_RE = re.compile(
    r"""(?P<trait_type>{TRAIT_TYPE_RE})
        (?:-(?P<trait_qualifier>{TRAIT_PART_RE}))?""".format(
            TRAIT_TYPE_RE=TRAIT_TYPE_RE.pattern,
            TRAIT_PART_RE=TRAIT_PART_RE.pattern),
    re.VERBOSE
)

TRAIT_KEY_RE = re.compile(
    r"""(?P<trait_type>{TRAIT_TYPE_RE})
        (?:-(?P<trait_qualifier>{TRAIT_PART_RE}))?
        (?::(?P<branch>{TRAIT_TYPE_RE}))?
        (?:\((?P<version>{TRAIT_PART_RE})\))?""".format(
            TRAIT_TYPE_RE=TRAIT_TYPE_RE.pattern,
            TRAIT_PART_RE=TRAIT_PART_RE.pattern),
    re.VERBOSE
)

def validate_trait_name(trait_name):
    if TRAIT_NAME_RE.fullmatch(trait_name) is None:
        raise ValueError("'%s' is not a valid trait_name" % trait_name)

def validate_trait_type(trait_type):
    if TRAIT_TYPE_RE.fullmatch(trait_type) is None:
        raise ValueError("'%s' is not a valid trait_type" % trait_type)

def validate_traitkey_part(traitkey_part):
    if TRAIT_PART_RE.fullmatch(traitkey_part) is None:
        raise ValueError("'%s' is not a valid trait_key part" % traitkey_part)


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

    @classmethod
    def as_trait_name(self, *args):
        if len(args) == 2:
            return self._make_trait_name(*args)
        # if len(args) == 0:
        #     if isinstance(self, object):
        #         return self._make_trait_name(self.trait_key, self.trait_qualifier)
        # TODO: Implement solutions for other cases.

    @classmethod
    def split_trait_name(cls, trait_key_like):
        tk = cls.as_traitkey(trait_key_like)
        return (tk.trait_type, tk.trait_qualifier)

    @staticmethod
    def _make_trait_name(trait_type, trait_qualifier):
        if trait_qualifier is None or trait_qualifier == '':
            return trait_type
        else:
            return "{trait_type}-{trait_qualifier}".format(
                trait_qualifier=trait_qualifier, trait_type=trait_type)

    @property
    def trait_name(self):
        return self._make_trait_name(self.trait_type, self.trait_qualifier)

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


        # try...except block to handle attempting to preload the trait. If the
        # preload fails, then we assume that the cleanup does not need to be called.
        try:

            # Preload the Trait if necessary.
            self._trait._load_incr()
        except DataNotAvailable:
            raise
        except Exception as e:
            log.exception("An exception occurred trying to preload Trait %s",
                          self._trait.trait_key
                          )
            raise DataNotAvailable("An unexpected error occurred trying to retrieve the requested data.")

        # Now, the Trait has been successfully preloaded. Here is another
        # try...except block, which will make sure the Trait is cleaned up
        # even if the TraitProperty can't be retrieved.

        try:
            # Call the actual user defined loader function to get the value of the TraitProperty.
            value = self._trait_property.fload(self._trait)
        except DataNotAvailable:
            raise
        except Exception as e:
            log.exception("An unexpected exception occurred trying to retrieve the TraitProperty %s of Trait %s",
                          self._trait_property.name,
                          self._trait.trait_key
                          )
            raise DataNotAvailable("An error occurred trying to retrieve the requested data.")
        finally:
            # Finally because we have definitely successfully run the
            # preload command, we must run the cleanup even if there was an error.

            # Cleanup the Trait if necessary.
            self._trait._load_decr()

        return value

# Register `BoundTraitProperty` as a subclass of `TraitProperty`. This makes
# `isinstance(value, TraitProperty)` work as expected for `TraitProperty`s that have
# been bound to their `Trait`.
TraitProperty.register(BoundTraitProperty)

def trait_property_from_fits_header(header_card_name, type, name):

    tp = TraitProperty(type=type, name=name)

    tp.fload = lambda self: self._header[header_card_name]
    tp.short_name = header_card_name

    # # @TODO: Providence information can't get filename currently...
    # tp.providence = "!: FITS-Header {{file: '{filename}' extension: '{extension}' header: '{card_name}'}}".format(
    #     card_name=header_card_name, extension=extension, filename='UNDEFINED'
    # )

    return tp
