import collections
import re
from operator import itemgetter

from ..descriptions import DescriptionsMixin

from .. import slogging
log = slogging.getLogger(__name__)
log.enable_console_logging()
log.setLevel(slogging.WARNING)


TRAIT_TYPE_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*')
TRAIT_QUAL_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.]*')
TRAIT_BRANCH_RE = TRAIT_QUAL_RE
TRAIT_VERSION_RE = TRAIT_QUAL_RE

TRAIT_NAME_RE = re.compile(
    r"""(?P<trait_type>{TRAIT_TYPE_RE})
        (?:-(?P<trait_qualifier>{TRAIT_QUAL_RE}))?""".format(
            TRAIT_TYPE_RE=TRAIT_TYPE_RE.pattern,
            TRAIT_QUAL_RE=TRAIT_QUAL_RE.pattern),
    re.VERBOSE
)

TRAIT_KEY_RE = re.compile(
    r"""(?P<trait_type>{TRAIT_TYPE_RE})
        (?:-(?P<trait_qualifier>{TRAIT_QUAL_RE}))?
        (?::(?P<branch>{TRAIT_BRANCH_RE}))?
        (?:\((?P<version>{TRAIT_VERSION_RE})\))?""".format(
            TRAIT_TYPE_RE=TRAIT_TYPE_RE.pattern,
            TRAIT_QUAL_RE=TRAIT_QUAL_RE.pattern,
            TRAIT_BRANCH_RE=TRAIT_BRANCH_RE.pattern,
            TRAIT_VERSION_RE=TRAIT_VERSION_RE.pattern),
    re.VERBOSE
)

def validate_trait_name(trait_name):
    if TRAIT_NAME_RE.fullmatch(trait_name) is None:
        raise ValueError("'%s' is not a valid trait_name" % trait_name)

def validate_trait_type(trait_type):
    if TRAIT_TYPE_RE.fullmatch(trait_type) is None:
        raise ValueError("'%s' is not a valid trait_type" % trait_type)

def validate_trait_qualifier(trait_qualifier):
    if TRAIT_QUAL_RE.fullmatch(trait_qualifier) is None:
        raise ValueError("'%s' is not a valid trait qualifier" % trait_qualifier)

def validate_trait_branch(trait_branch):
    if TRAIT_BRANCH_RE.fullmatch(trait_branch) is None:
        raise ValueError("'%s' is not a valid trait branch" % trait_branch)

def validate_trait_version(trait_version):
    if TRAIT_VERSION_RE.fullmatch(trait_version) is None:
        raise ValueError("'%s' is not a valid trait version" % trait_version)




class TraitKey(tuple):
    """TraitKey(trait_type, trait_name, version, object_id)"""

    # Originally, this class was created using the following command:
    #     TraitKey = collections.namedtuple('TraitKey', ['trait_type', 'trait_name', 'object_id'], verbose=True)


    __slots__ = ()

    _fields = ('trait_type', 'trait_qualifier', 'version', 'branch')

    def __new__(_cls, trait_type, trait_qualifier=None, branch=None, version=None):
        """Create new instance of TraitKey(trait_type, trait_qualifier, branch, version)"""
        validate_trait_type(trait_type)
        if trait_qualifier is not None:
            validate_trait_qualifier(trait_qualifier)
        if branch is not None:
            validate_trait_branch(branch)
        if version is not None:
            validate_trait_version(version)
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

    trait_type = property(itemgetter(0), doc='Trait type')

    trait_qualifier = property(itemgetter(1), doc='Trait qualifier')

    branch = property(itemgetter(2), doc='Branch')

    version = property(itemgetter(3), doc='Version')


class Branch(DescriptionsMixin):

    # This tells the DescriptionsMixin to provide separate descriptions for each instance of this class.
    descriptions_allowed = 'instance'

    def __init__(self, name, pretty_name=None, description=None, versions=None):
        if description is not None:
            self.set_description(description)
        if pretty_name is not None:
            self.set_pretty_name(pretty_name)
        self.name = name

        if versions is not None:
            self.versions = set(versions)
        else:
            self.versions = {None}

    def __str__(self):
        return self.name
