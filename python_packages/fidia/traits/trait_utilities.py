"""

Trait Utilities: Various tools to make Traits work.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Dict, List, Type, Union, Tuple, Any
import fidia

# Python Standard Library Imports
from collections import OrderedDict
import re
from operator import itemgetter

# Other Library Imports
from cached_property import cached_property
import sqlalchemy as sa
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection, mapped_collection

# FIDIA Imports
from fidia.exceptions import *
import fidia.base_classes as bases
from ..utilities import DefaultsRegistry, RegexpGroup, snake_case, MultiDexDict, fidia_classname
from ..descriptions import DescriptionsMixin

# Logging import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()


__all__ = [
    # Trait Definitions:
    'TraitProperty', 'SubTrait',
    # Trait Mappings:
    'TraitMapping', 'TraitPointer', 'TraitPropertyMapping', 'SubTraitMapping',
    'TraitManager',
    # Trait Identification:
    'TraitKey', 'TraitPath', 'validate_trait_name'
]


# ___  __         ___     __   ___  ___          ___    __
#  |  |__)  /\  |  |     |  \ |__  |__  | |\ | |  |  | /  \ |\ |
#  |  |  \ /~~\ |  |     |__/ |___ |    | | \| |  |  | \__/ | \|
#


class TraitProperty(DescriptionsMixin):
    """Defines a 'slot' for a Trait property (reference to a column)."""
    allowed_types = RegexpGroup(
        'string',
        'float',
        'int',
        re.compile(r"string\.array\.\d+"),
        re.compile(r"float\.array\.\d+"),
        re.compile(r"int\.array\.\d+"),
        # # Same as above, but with optional dimensionality
        # re.compile(r"string\.array(?:\.\d+)?"),
        # re.compile(r"float\.array(?:\.\d+)?"),
        # re.compile(r"int\.array(?:\.\d+)?"),
    )

    catalog_types = [
        'string',
        'float',
        'int'
    ]

    non_catalog_types = RegexpGroup(
        re.compile(r"string\.array\.\d+"),
        re.compile(r"float\.array\.\d+"),
        re.compile(r"int\.array\.\d+")
        # # Same as above, but with optional dimensionality
        # re.compile(r"string\.array(?:\.\d+)?"),
        # re.compile(r"float\.array(?:\.\d+)?"),
        # re.compile(r"int\.array(?:\.\d+)?"),
    )

    descriptions_allowed = 'instance'

    def __init__(self, dtype, n_dim=0, optional=False, name=None):
        self.dtype = dtype
        self.n_dim = n_dim
        self.optional = optional
        self.name = name
        self._type = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._type = value

    # noinspection PyProtectedMember
    def __get__(self, trait, trait_class):
        # type: (fidia.Trait, Type[fidia.Trait]) -> Any
        if trait is None:
            return self
        else:
            if self.name is None:
                raise TraitValidationError("TraitProperty not correctly initialised.")
            column_id = trait.trait_mapping.trait_property_mappings[self.name].id
            result = trait._get_column_data(column_id)
            setattr(trait, self.name, result)
            return result

    def __repr__(self):
        return "<TraitProperty {}>".format(self.name)

class SubTrait(object):
    """Defines a 'slot' for a sub-Trait."""
    def __init__(self, trait_class, optional=False):
        # type: (Type[fidia.Trait], bool) -> None
        from .base_trait import Trait
        assert issubclass(trait_class, Trait)
        self.trait_class = trait_class
        self.optional = optional
        self.name = None  # type: str

    def __get__(self, parent_trait, parent_trait_class):
        # type: (fidia.Trait, Type[fidia.Trait]) -> Any
        if parent_trait is None:
            return self
        else:
            if self.name is None:
                raise TraitValidationError("TraitProperty not correctly initialised.")
            if self.name not in parent_trait.trait_mapping.sub_trait_mappings:
                if self.optional:
                    raise DataNotAvailable("Optional sub-trait %s not provided." % self.name)
                else:
                    raise TraitValidationError("Trait definition missing mapping for required sub-trat %s" % self.name)
            trait_mapping = parent_trait.trait_mapping.sub_trait_mappings[self.name]  # type: SubTraitMapping
            result = self.trait_class(sample=parent_trait.sample, trait_key=parent_trait.trait_key,
                                      astro_object=parent_trait.astro_object,
                                      trait_mapping=trait_mapping)
            return result


# ___  __         ___       __   ___      ___    ___    __       ___    __
#  |  |__)  /\  |  |     | |  \ |__  |\ |  |  | |__  | /  `  /\   |  | /  \ |\ |
#  |  |  \ /~~\ |  |     | |__/ |___ | \|  |  | |    | \__, /~~\  |  | \__/ | \|
#

TRAIT_NAME_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9_]*')
TRAIT_BRANCH_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.]*')
TRAIT_VERSION_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.]*')


TRAIT_KEY_RE = re.compile(
    r"""(?P<trait_name>{TRAIT_NAME_RE})
        (?::(?P<branch>{TRAIT_BRANCH_RE}))?
        (?:\((?P<version>{TRAIT_VERSION_RE})\))?""".format(
            TRAIT_NAME_RE=TRAIT_NAME_RE.pattern,
            TRAIT_BRANCH_RE=TRAIT_BRANCH_RE.pattern,
            TRAIT_VERSION_RE=TRAIT_VERSION_RE.pattern),
    re.VERBOSE
)

# This alternate TraitKey regular expression will match strings using the
# "hyphen-only" notation.
TRAIT_KEY_ALT_RE = re.compile(
    r"""(?P<trait_name>{TRAIT_NAME_RE})
        (?:-(?P<branch>{TRAIT_BRANCH_RE})?
            (?:-(?P<version>{TRAIT_VERSION_RE})?)?
        )?""".format(
            TRAIT_NAME_RE=TRAIT_NAME_RE.pattern,
            TRAIT_BRANCH_RE=TRAIT_BRANCH_RE.pattern,
            TRAIT_VERSION_RE=TRAIT_VERSION_RE.pattern),
    re.VERBOSE
)

def validate_trait_name(trait_type):
    """Check if a string meets the formatting requirements for a trait name."""
    if TRAIT_NAME_RE.fullmatch(trait_type) is None:
        raise ValueError("'%s' is not a valid trait name" % trait_type)

def validate_trait_branch(trait_branch):
    """Check if a string meets the formatting requirements for a trait branch."""
    if TRAIT_BRANCH_RE.fullmatch(trait_branch) is None:
        raise ValueError("'%s' is not a valid trait branch" % trait_branch)

def validate_trait_version(trait_version):
    """Check if a string meets the formatting requirements for a trait version."""
    if TRAIT_VERSION_RE.fullmatch(trait_version) is None:
        raise ValueError("'%s' is not a valid trait version" % trait_version)


# noinspection PyInitNewSignature
class TraitKey(tuple):
    """TraitKey(trait_name, version, object_id)"""

    # Originally, this class was created using the following command:
    #     TraitKey = collections.namedtuple('TraitKey', ['trait_type', 'trait_name', 'object_id'], verbose=True)

    __slots__ = ()

    _fields = ('trait_name', 'version', 'branch')

    trait_name = property(itemgetter(0), doc='Trait name')
    branch = property(itemgetter(1), doc='Branch')
    version = property(itemgetter(2), doc='Version')

    # noinspection PyArgumentList
    def __new__(cls, trait_name, branch=None, version=None):
        """Create new instance of TraitKey(trait_type, trait_qualifier, branch, version)"""
        validate_trait_name(trait_name)
        if branch is not None:
            validate_trait_branch(branch)
        if version is not None:
            validate_trait_version(version)
        return tuple.__new__(cls, (trait_name, branch, version))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__):
        """Make a new TraitKey object from a sequence or iterable"""
        result = new(cls, iterable)
        if len(result) not in (1, 2, 3):
            raise TypeError('Expected 1-3 arguments, got %d' % len(result))
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
                return cls(trait_name=match.group('trait_name'),
                           branch=match.group('branch'),
                           version=match.group('version'))
            match = TRAIT_KEY_ALT_RE.fullmatch(key)
            if match:
                return cls(trait_name=match.group('trait_name'),
                           branch=match.group('branch'),
                           version=match.group('version'))
        raise KeyError("Cannot parse key '{}' into a TraitKey".format(key))


    def __repr__(self):
        """Return a nicely formatted representation string"""
        return 'TraitKey(trait_name=%r, branch=%r, version=%r)' % self

    def _asdict(self):
        """Return a new OrderedDict which maps field names to their values"""
        return OrderedDict(zip(self._fields, self))

    def replace(self, **kwargs):
        """Return a new TraitKey object replacing specified fields with new values"""
        # noinspection PyTypeChecker
        result = self._make(map(kwargs.pop, ('trait_name', 'branch', 'version'), self))
        if kwargs:
            raise ValueError('Got unexpected field names: %r' % kwargs.keys())
        return result

    def ashyphenstr(self):
        s = self.trait_name
        if self.branch or self.version:
            s += "-"
            if self.branch:
                s += self.branch
            if self.version:
                s += "-" + self.version
        return s

    def __getnewargs__(self):
        """Return self as a plain tuple.  Used by copy and pickle."""
        return tuple(self)

    __dict__ = property(_asdict)

    def __getstate__(self):
        """Exclude the OrderedDict from pickling"""
        pass

    def __str__(self):
        trait_string = self.trait_name
        if self.branch:
            trait_string += ":" + self.branch
        if self.version:
            trait_string += "(" + self.version + ")"
        return trait_string


class TraitPath(tuple):
    """A class to handle full paths to Traits.

    The idea is that a sequence of TraitKeys can uniquely identify a Trait
    within an archive. This class provides a convenient way to bring such a
    sequence of TraitKeys together, and manage such sequences.

    """

    # __slots__ = ()

    # noinspection PyArgumentList
    def __new__(cls, trait_path_tuple=None, trait_property=None):
        log.debug("Creating new TraitPath with tuple %s and property %s", trait_path_tuple, trait_property)

        if isinstance(trait_path_tuple, str):
            trait_path_tuple = trait_path_tuple.split("/")

        if trait_path_tuple is None or len(trait_path_tuple) == 0:
            return tuple.__new__(cls, ())

        validated_tk_path = [TraitKey.as_traitkey(elem) for elem in trait_path_tuple]
        new = tuple.__new__(cls, validated_tk_path)
        new.trait_property_name = trait_property
        return new

    def __repr__(self):
        return "TraitPath((%s), %s)" % (", ".join([repr(tk) for tk in self]) + ", ", self.trait_property_name)

    def __str__(self):
        s = "/".join([str(tk) for tk in self])
        if self.trait_property_name:
            s += "/" + self.trait_property_name
        return s

    @staticmethod
    def as_traitpath(trait_path):
        if isinstance(trait_path, TraitPath):
            return trait_path
        else:
            return TraitPath(trait_path)

    def get_trait_class_for_archive(self, archive):
        trait = archive
        for elem in self:
            if hasattr(trait, 'sub_traits'):
                # Looking at trait
                updated_tk = trait.sub_traits.update_key_with_defaults(elem)
                trait = trait.sub_traits.retrieve_with_key(updated_tk)
            else:
                # Looking at archive:
                updated_tk = trait.available_traits.update_key_with_defaults(elem)
                trait = trait.available_traits.retrieve_with_key(updated_tk)
        return trait

    def get_trait_property_for_archive(self, archive):

        trait_class = self.get_trait_class_for_archive(archive)
        if self.trait_property_name is None:
            if not hasattr(trait_class, 'value'):
                raise FIDIAException()
            else:
                tp_name = 'value'
        else:
            tp_name = self.trait_property_name
        trait_property = getattr(trait_class, tp_name)
        return trait_property

    def get_trait_for_object(self, astro_object):
        # type: (fidia.AstronomicalObject) -> fidia.Trait
        trait = astro_object
        for elem in self:
            trait = trait[elem]
        return trait

    def get_trait_property_for_object(self, astro_object):
        # type: (fidia.AstronomicalObject) -> fidia.Trait


        trait = self.get_trait_for_object(astro_object)
        if self.trait_property_name is None:
            if not hasattr(trait, 'value'):
                raise FIDIAException()
            else:
                tp_name = 'value'
        else:
            tp_name = self.trait_property_name
        trait_property = getattr(trait, tp_name)

        return trait_property

    def get_trait_property_value_for_object(self, astro_object):
        # type: (fidia.AstronomicalObject) -> Any

        trait_property = self.get_trait_property_for_object(astro_object)

        return trait_property.value



class BranchesVersions(dict):

    def get_pretty_name(self, item):
        key = self.get_full_key(item)
        if isinstance(key, tuple):
            if len(key) > 1:
                return key[1]
            else:
                return key[0]
        else:
            return key

    def get_description(self, item):
        key = self.get_full_key(item)
        if isinstance(key, tuple) and len(key) > 2:
            return key[2]
        else:
            return ""

    def get_version_pretty_name(self, branch, version):
        full_item = self.get_full_item(branch)
        for version_tuple in full_item:
            if isinstance(version_tuple, tuple) and version_tuple[0] == version:
                if len(version_tuple) > 1:
                    return version_tuple[1]
                else:
                    # Fall back to simply returning the version ID
                    return version_tuple[0]
            elif version_tuple == version:
                return version_tuple
        # Version not found in the set of all versions.
        raise KeyError("Version '%s' not found" % version)


    def get_version_description(self, branch, version):
        full_item = self.get_full_item(branch)
        for version_tuple in full_item:
            if isinstance(version_tuple, tuple) and version_tuple[0] == version:
                if len(version_tuple) > 2:
                    return version_tuple[2]
                else:
                    # Return empty string if no description.
                    return ""
            elif version_tuple == version:
                return ""
        # Version not found in the set of all versions.
        raise KeyError("Version '%s' not found")

    def name_keys(self):
        for key in self.keys():
            if isinstance(key, tuple):
                yield key[0]
            else:
                yield key

    def get_full_key(self, branch):
        if branch not in self.keys():
            for key in self.keys():
                if isinstance(key, tuple) and branch == key[0]:
                    return key
            # Have iterated through all keys and none matched.
            raise KeyError("Branch '%s' not found" % branch)
        else:
            return branch

    def get_full_item(self, item):
        key = self.get_full_key(item)
        return super(BranchesVersions, self).__getitem__(key)


    def __getitem__(self, item):
        full_item = self.get_full_item(item)
        # The full item for a branch will be a set of either version identifiers
        # or tuples with (verid, prettyname, desc)
        # Return only the first items of each tuple.
        return {(i[0] if isinstance(i, tuple) else i) for i in full_item}

    def __contains__(self, item):
        return item in self.name_keys()

    def __iter__(self):
        return self.name_keys()

    def has_single_branch_and_version(self):
        """Test if this branch version dictionary has only one branch and one version.

        In this case, it is effectively its own default.

        """

        values = self.values()
        # Check for single branch
        res = len(values) == 1
        # Check for single version
        versions = list(values)
        res = res and len(versions[0]) == 1

        return res

    def as_defaults(self):
        """Return a copy of this as a DefaultsRegistry"""

        if not self.has_single_branch_and_version():
            return None

        branch = list(self.name_keys())[0]

        versions_set = list(self.values())[0]
        version = list(versions_set)[0]

        return DefaultsRegistry(version_defaults={branch: version})



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

# ___  __         ___     __   ___  __   __                    __
#  |  |__)  /\  |  |     |__) |__  /__` /  \ |    \  / | |\ | / _`
#  |  |  \ /~~\ |  |     |  \ |___ .__/ \__/ |___  \/  | | \| \__>
#
class TraitPointer(bases.TraitPointer):
    """Provides machinery to identify and instanciate a `Trait` on an `AstronomicalObject`.


        gami_sample['9352'].dmu['stellarMass(v09)'].table['StellarMasses(v08)'].logmstar
                            ---                     -----
                                   TraitPointers

    TraitPointers have links to:
    - The class of `Trait` they will instanciate
    - The `TraitRegistry` (presumably on the `Sample` object)
    - The `AstronomicalObject` for which they will create a `Trait`.

    This class provides validation and normalisation of a user-provided `TraitKey`, and
    and then handles creating the corresponding `Trait` instance and ensuring it is valid.

    The machinery of interpreting the user plugin into a mapping of Columns into Traits
    is in the `TraitRegistry`. The machinery for creating the actual links from a Trait
    instance to a Column instance is in `BaseTrait._link_columns()`. Therefore,
    `TraitPointer` is fairly thin.

    """

    def __init__(self, name, sample, astro_object, trait_mapping=None, trait_registry=None):
        # type: (str, fidia.Sample, fidia.AstronomicalObject, TraitMapping, TraitManager) -> None
        self.name = name
        self.sample = sample
        self.astro_object = astro_object
        self.trait_mapping = trait_mapping
        self.trait_registry = trait_registry

    def __getitem__(self, item):
        tk = TraitKey.as_traitkey(item)

        if self.trait_mapping is not None:
            tk = self.trait_mapping.update_trait_key_with_defaults(tk)
            mapping = self.trait_mapping.named_sub_mappings[self.name, str(tk)]  # type: TraitMapping
        else:
            mapping = self.sample.trait_mappings[self.name, str(tk)]  # type: TraitMapping
        trait_class = mapping.trait_class
        # assert issubclass(trait_class, (fidia.Trait, fidia.TraitCollection))
        trait = trait_class(sample=self.sample, trait_key=tk,
                            astro_object=self.astro_object,
                            trait_mapping=mapping)

        # @TODO: Object Caching?

        return trait

    def __str__(self):
        "TraitPointer: %s" % self.trait_mapping


# ___  __         ___                __   __          __      __   __
#  |  |__)  /\  |  |      |\/|  /\  |__) |__) | |\ | / _`    |  \ |__)
#  |  |  \ /~~\ |  |      |  | /~~\ |    |    | | \| \__>    |__/ |__)
#

class TraitManager(bases.TraitMappingDatabase, bases.SQLAlchemyBase):
    """Trait Managers handle mappings of Trait Paths to columns.

    An archive module can define Traits and TraitCollections, which are then registered
    against a TraitManager. The TraitManager will introspect the trait classes provided
    in order to build up the schema.

    As part of the introspection, the registry will also validate that each Trait's slots
    have been correctly filled (e.g. with another trait or a column of a particular type).

    The TraitManager keeps a list of all valid TraitPaths that it knows about.

    ???
    As part of registration, the Manager will update each TraitClass with information about
    where it appears in the hierarchy.

    ???
    It also handles instanciating traits as required when they are looked up

    When Traits are instanciated, they are provided with the trait key used to instanciate
    them, the archive instance containing them, and the trait path leading to them.

    """

    # @TODO: Does not check that a Trait's slots have been correctly filled.

    __tablename__ = "trait_managers"

    _db_id = sa.Column(sa.Integer, sa.Sequence('trait_managers_seq'), primary_key=True)
    host_archive = relationship('Archive', back_populates='trait_manager', uselist=False)
    # _mappings = relationship('TraitMapping')  # type: List[TraitMapping]

    def __init__(self, session=None):
        raise Exception("TraitManagers are deprecated!")
        # self._mappings = []  # type: List[TraitMapping]
        self.linked_mappings = []  # type: List[TraitManager]
        self._local_trait_mappings = MultiDexDict(2)  # type: Dict[Tuple[str, str], TraitMapping]
        # @TODO: Consider removing the duplication from _mappings and _local_trait_mappings
        self.collection_mappings = dict()
        self.host = None
        self.session = session

    def link_database(self, other_database, index=-1):
        # type: (TraitManager, int) -> None
        assert isinstance(other_database, TraitManager)
        self.linked_mappings.insert(index, other_database)

    def register_mapping(self, mapping):
        # type: (TraitMapping) -> None
        if isinstance(mapping, TraitMapping):
            mapping.validate()
            key = mapping.key()
            log.debug("Registering mapping for key %s", key)
            # Check if key already exists in this database
            if key in self._local_trait_mappings:
                raise FIDIAException("Attempt to add/change an existing mapping")
            # Check if key already exists in a linked database
            for sub_db in self.linked_mappings:
                if key in sub_db.trait_mappings:
                    log.warning("New mapping %s shadows existing mapping %s in %s",
                                mapping, sub_db.trait_mappings[key], sub_db.host)
            self._local_trait_mappings[key] = mapping
            # @TODO: Also link up superclasses of the provided Trait to the FIDIA level.
        else:
            raise ValueError("TraitManager can only register a TraitMapping, got %s"
                             % mapping)

        # If we are connected to the persistence database, add this mapping:
        if self.session is not None:
            self.session.add(mapping)

        self._mappings.append(mapping)

    @property
    def trait_mappings(self):
        result = MultiDexDict(2)
        for sub_db in self.linked_mappings:
            result.update(sub_db.trait_mappings)
        result.update(self._local_trait_mappings)
        return result

    def register_mapping_list(self, trait_mapping_list):
        # type: (List[fidia.traits.TraitMapping]) -> None
        """Simply calls `.register_trait_mapping` for each item in the supplied list."""
        for mapping in trait_mapping_list:
            self.register_mapping(mapping)

    def get_trait_mappings(self):

        # @TODO: This raises an exception if there are duplicate TraitMapping entries in the system.

        trait_mapping_keys_returned = set()

        for tm in self._mappings:
            string_key = "-".join(tm.key())
            if string_key in trait_mapping_keys_returned:
                raise FIDIAException('Duplicate TraitMappings found: %s' % string_key)
            trait_mapping_keys_returned.add(string_key)
            yield tm

        for sub_database in self.linked_mappings:
            for tm in sub_database._mappings:
                string_key = "-".join(tm.key())
                if string_key in trait_mapping_keys_returned:
                    # @TODO: This should perhaps be changed to simply skip shadowed mappings
                    raise FIDIAException('Duplicate TraitMappings found: %s' % string_key)
                yield tm


class MappingBranchVersionHandling:
    """Mixin class to provide Branch and version handling to Mappings."""

    def __init__(self, branches_versions=None, branch_version_defaults=None):
        self.branches_versions = self._init_branches_versions(branches_versions)
        self._branch_version_defaults = self._init_default_branches_versions(branch_version_defaults)

    @staticmethod
    def _init_branches_versions(branches_versions):
        # type: (Any) -> Union[dict, None]
        """Interpret the provided branch and version information and return a valid result for TraitMappings.

        This basically checks that the provided input can be interpreted as either:
            None:
                No branch and version information is allowed for this Trait.
            dict of lists of versions keyed by the associated branch:
                Only these branches and versions are explicitly allowed

        @TODO: Perhaps in future, support an "Any" option which would allow
        tokenized branch and version information in the column identifiers.

        """
        if branches_versions is None:
            return None
        else:
            if not isinstance(branches_versions, dict):
                raise ValueError(
                    "branches_versions keyword must be a dictionary or none, got: %s" % branches_versions)
            for branch in branches_versions:
                validate_trait_branch(branch)
                for version in branches_versions[branch]:
                    validate_trait_version(version)
            return branches_versions

    def _init_default_branches_versions(self, branch_version_defaults):
        # type: (Any) -> Union[None, DefaultsRegistry]
        if self.branches_versions is None:
            return None
        if branch_version_defaults is None:
            # Try to construct defaults information from the ordering of the branches_versions information
            version_defaults = dict()
            for branch in self.branches_versions:
                version_defaults[branch] = self.branches_versions[branch][0]
            if isinstance(self.branches_versions, OrderedDict):
                default_branch = next(iter(self.branches_versions))
            else:
                default_branch = None
            return DefaultsRegistry(default_branch, version_defaults)
        if isinstance(branch_version_defaults, DefaultsRegistry):
            return branch_version_defaults
        raise ValueError("Branch and version defaults not valid, got: %s" % branch_version_defaults)


    def update_trait_key_with_defaults(self, trait_key):
        """Return TraitKey with branch and version populated from defaults.

        Check the provided trait key, and if either the branch or version
        have not been provided (None), then return an updated version based on
        the contents of the defaults registry (if possible)

        """
        # Ensure we are working with a full TraitKey object (or convert if necessary)
        tk = TraitKey.as_traitkey(trait_key)

        if self.branches_versions is None:
            return TraitKey(tk.trait_name)

        log.debug("Updating TraitKey '%s' with defaults" % str(trait_key))

        # If the branch has not been specified, get the default from the DefaultsRegistry for this trait_name
        if tk.branch is None:
            tk = tk.replace(branch=self._branch_version_defaults.branch)
            # @TODO: Handle cases where this branch is not in the defaults registry.
            log.debug("Branch not supplied for '%s', using default '%s'", tk.trait_name, tk.branch)

        # If the version has not been specified, get the default from the DefaultsRegistry for this trait_name
        if tk.version is None:
            tk = tk.replace(version=self._branch_version_defaults.version(tk.branch))
            log.debug("Version not supplied for '%s', using default '%s'", tk.trait_name, tk.version)

        return tk


class MappingBase:

    _reconstructed = None

    def validate(self):
        raise NotImplementedError()


class TraitMappingBase(MappingBase, bases.SQLAlchemyBase):

    __tablename__ = "trait_mappings"  # Note this table is shared with TraitMapping and SubTraitMapping classes.

    _db_type = sa.Column('type', sa.String(50))
    __mapper_args__ = {'polymorphic_on': "_db_type"}

    _database_id = sa.Column(sa.Integer, sa.Sequence('trait_mapping_seq'), primary_key=True)
    _db_trait_class = sa.Column(sa.String)
    _parent_id = sa.Column(sa.Integer, sa.ForeignKey('trait_mappings._database_id'))

    trait_property_mappings = relationship("TraitPropertyMapping", back_populates="_trait_mappings",
                                           collection_class=attribute_mapped_collection('name'))  # type: Dict[str, TraitPropertyMapping]

    def __init__(self):
        self._trait_class = None  # type: Type[fidia.traits.BaseTrait]


    def _reconstruct_trait_class(self):
        if '.' in self._db_trait_class:
            # this is an external Trait type, so we must construct it:
            trait_type = exec(self._db_trait_class)
            assert issubclass(trait_type, fidia.traits.BaseTrait), \
                "Error reconstructing TraitMapping from database: Unknown external trait class."
            self._trait_class = trait_type
        else:
            # This is a FIDIA trait
            trait_type = getattr(fidia.traits, self._db_trait_class)
            assert issubclass(trait_type, fidia.traits.BaseTrait), \
                "Error reconstructing TraitMapping from database: Unknown FIDIA trait class."
            self._trait_class = trait_type


    @property
    def trait_class(self):
        if getattr(self, '_trait_class', None) is None:
            self._reconstruct_trait_class()
        return self._trait_class

    @trait_class.setter
    def trait_class(self, value):
        assert issubclass(value, fidia.traits.BaseTrait)
        self._db_trait_class = fidia_classname(value)
        self._trait_class = value


class TraitMapping(TraitMappingBase, MappingBranchVersionHandling):
    """Representation of the schema of a Trait.

    This can be thought of as a link from a class and name to a set of onward links.

    """

    __mapper_args__ = {'polymorphic_identity': 'TraitMapping'}
    _db_trait_key = sa.Column(sa.String)
    _archive_id = sa.Column(sa.Integer, sa.ForeignKey('archives._db_id'))
    # host_manager = relationship(TraitManager)  # type: TraitManager
    sub_trait_mappings = relationship(
        'SubTraitMapping', # back_populates="_trait_mappings",
        collection_class=attribute_mapped_collection('name'))  # type: Dict[str, SubTraitMapping]
    named_sub_mappings = relationship(
        'TraitMapping', # back_populates="_trait_mappings",
        collection_class=mapped_collection(lambda o: o.key()))  # type: Dict[Tuple[str, str], TraitMapping]


    @reconstructor
    def __db_init__(self):
        self._reconstruct_trait_class()
        self._reconstruct_trait_key()
        self._reconstructed = True

    def _reconstruct_trait_key(self):
        self._trait_key = TraitKey.as_traitkey(self._db_trait_key)

    def __init__(self, trait_class, trait_key, mappings, branches_versions=None, branch_version_defaults=None):
        # type: (Type[fidia.traits.BaseTrait], str, List[Union[TraitMapping, TraitPropertyMapping, SubTraitMapping]]) -> None

        # Initialise internal variables
        self._reconstructed = False
        self._trait_key = None  # type: fidia.traits.TraitKey

        self.trait_class = trait_class
        self.trait_key = TraitKey.as_traitkey(trait_key)

        # Super calls
        #     These are individual because not all super initialisers
        #     need to be called, and the arguments are different.
        TraitMappingBase.__init__(self)
        MappingBranchVersionHandling.__init__(self, branches_versions, branch_version_defaults)
        # @TODO: Branch and versions are still tricky: what if different TraitMappings define different b's and v's?

        self.sub_trait_mappings = dict()  # type: Dict[str, SubTraitMapping]

        for item in mappings:
            if isinstance(item, TraitPropertyMapping):
                self.trait_property_mappings[item.name] = item
            elif isinstance(item, SubTraitMapping):
                if issubclass(self.trait_class, fidia.TraitCollection):
                    raise ValueError("TraitCollections don't support sub-Traits")
                self.sub_trait_mappings[item.name] = item
            elif isinstance(item, TraitMapping):
                if issubclass(self.trait_class, fidia.Trait):
                    raise ValueError("Named sub-traits not yet supported for Traits.")
                self.named_sub_mappings[item.key()] = item
            else:
                raise ValueError("TraitMapping accepts only TraitPropertyMappings and SubTraitMappings, got %s" % item)

    @cached_property
    def name(self):
        # @TODO: This will break with external Trait names.
        #   To fix this, we should modify fidia_classname to have the option to
        #   only return the classname, but guarantee that there are no conflicts
        #   with existing FIDIA types.
        return snake_case(fidia_classname(self.trait_class))

    @property
    def trait_key(self):
        if getattr(self, '_trait_key', None) is None:
            self._reconstruct_trait_key()
        return self._trait_key

    @trait_key.setter
    def trait_key(self, value):
        tk = TraitKey.as_traitkey(value)
        self._db_trait_key = str(tk)
        self._trait_key = tk

    def validate(self):
        # Check that all required (not optional) TraitProperties are defined in the schema:
        for tp in self.trait_class.trait_properties():
            if tp.name not in self.trait_property_mappings and not tp.optional:
                raise TraitValidationError("Trait %s missing required TraitProperty %s in definition" % (self, tp.name))

    def key(self):
        return self.name, str(self.trait_key)

    def __repr__(self):
        if self._reconstructed is None:
            return "Unreconstructed " + super(TraitMapping, self).__repr__()

        mappings = list(self.trait_property_mappings.values())
        return ("TraitMapping(trait_class=%s, trait_key='%s', mappings=%s)" %
                (fidia_classname(self.trait_class), str(self.trait_key), repr(mappings)))


class SubTraitMapping(TraitMappingBase):

    __mapper_args__ = {'polymorphic_identity': 'SubTraitMapping'}

    name = sa.Column(sa.String)

    def __init__(self, sub_trait_name, trait_class, mappings):
        # type: (str, Type[fidia.Trait], List[Union[TraitMapping, TraitPropertyMapping, SubTraitMapping]]) -> None
        assert issubclass(trait_class, fidia.traits.BaseTrait)
        self.trait_class = trait_class
        self.name = sub_trait_name
        # self._mappings = mappings

        # Super calls
        #     These are individual because not all super initialisers
        #     need to be called, and the arguments are different.
        TraitMappingBase.__init__(self)


        self.sub_trait_mappings = dict()  # type: Dict[str, SubTraitMapping]

        for item in mappings:
            if isinstance(item, TraitPropertyMapping):
                self.trait_property_mappings[item.name] = item
            elif isinstance(item, SubTraitMapping):
                self.sub_trait_mappings[item.name] = item
            elif isinstance(item, TraitMapping):
                raise ValueError("Named subtraits not supported for sub-Traits.")
            else:
                raise ValueError("SubTraitMapping accepts only TraitPropertyMappings and SubTraitMappings, got %s" % item)

    def validate(self):
        pass

    def __repr__(self):
        mappings = list(self.trait_property_mappings.values())
        return ("SubTraitMapping(sub_trait_name=%s, trait_class=%s, mappings=%s)" %
                (repr(self.name), fidia_classname(self.trait_class), repr(mappings)))


class TraitPropertyMapping(bases.SQLAlchemyBase, MappingBase):

    # Database fields and setup (SQLAlchemy)
    __tablename__ = "trait_property_mappings"
    database_id = sa.Column(sa.Integer, sa.Sequence('trait_mapping_seq'), primary_key=True)
    name = sa.Column(sa.String)
    id = sa.Column(sa.String)
    _trait_mappings = relationship("TraitMappingBase", back_populates="trait_property_mappings")
    _trait_mapping_id = sa.Column(sa.Integer, sa.ForeignKey('trait_mappings._database_id'))

    def __init__(self, property_name, column_id):
        # type: (str, str) -> None
        self.name = property_name
        self.id = column_id

    def validate(self):
        pass

    def __repr__(self):
        return ("TraitPropertyMapping(%s, %s)" %
                (repr(self.name), repr(self.id)))

