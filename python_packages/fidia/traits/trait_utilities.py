"""

Trait Utilities: Various tools to make Traits work.

"""
from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Dict, List, Type, Union, Tuple, Any
import fidia

# Python Standard Library Imports
from itertools import product
from collections import OrderedDict
import re
from operator import itemgetter

# Other Library Imports

# FIDIA Imports
from fidia.exceptions import *
import fidia.base_classes as bases
from ..utilities import DefaultsRegistry, SchemaDictionary, is_list_or_set, RegexpGroup
from ..descriptions import DescriptionsMixin

# Logging import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


__all__ = [
    # Trait Definitions:
    'TraitProperty', 'SubTrait',
    # Trait Mappings:
    'TraitMapping', 'TraitPointer', 'TraitCollectionMapping', 'TraitPropertyMapping', 'SubTraitMapping',
    'TraitMappingDatabase',
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
            column_id = trait.trait_schema[self.name]
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
            if self.name not in parent_trait.trait_schema:
                if self.optional:
                    raise DataNotAvailable("Optional sub-trait %s not provided." % self.name)
                else:
                    raise TraitValidationError("Trait definition missing mapping for required sub-trat %s" % self.name)
            trait_mapping = parent_trait.trait_schema[self.name]  # type:
            result = self.trait_class(sample=parent_trait.sample, trait_key=parent_trait.trait_key,
                                      astro_object=parent_trait.astro_object,
                                      trait_registry=parent_trait.sample.trait_mappings,
                                      trait_schema=trait_mapping.trait_schema)
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

    def __new__(cls, trait_name, branch=None, version=None):
        """Create new instance of TraitKey(trait_type, trait_qualifier, branch, version)"""
        validate_trait_name(trait_name)
        if branch is not None:
            validate_trait_branch(branch)
        if version is not None:
            validate_trait_version(version)
        return tuple.__new__(cls, (trait_name, branch, version))

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
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
                           branch=       match.group('branch'),
                           version=match.group('version'))
        raise KeyError("Cannot parse key '{}' into a TraitKey".format(key))


    def __repr__(self):
        """Return a nicely formatted representation string"""
        return 'TraitKey(trait_name=%r, branch=%r, version=%r)' % self

    def _asdict(self):
        """Return a new OrderedDict which maps field names to their values"""
        return OrderedDict(zip(self._fields, self))

    def replace(self, **kwds):
        """Return a new TraitKey object replacing specified fields with new values"""
        result = self._make(map(kwds.pop, ('trait_name', 'branch', 'version'), self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
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

    def __new__(cls, trait_path_tuple=None, trait_property=None):
        log.debug("Creating new TraitPath with tuple %s and property %s", trait_path_tuple, trait_property)

        if isinstance(trait_path_tuple, str):
            trait_path_tuple = trait_path_tuple.split("/")

        if trait_path_tuple is None or len(trait_path_tuple) == 0:
            return tuple.__new__(cls, tuple())

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
        # type: (fidia.AstronomicalObject) -> fidia.Trait

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

    def __init__(self, sample, astro_object, trait_mapping, trait_registry):
        # type: (fidia.Sample, fidia.AstronomicalObject, TraitMapping, TraitMappingDatabase) -> None
        self.sample = sample
        self.astro_object = astro_object
        self.trait_mapping = trait_mapping
        self.trait_registry = trait_registry
        self.trait_class = trait_mapping.trait_class
        assert issubclass(self.trait_class, fidia.traits.BaseTrait)

    def __getitem__(self, item):
        tk = TraitKey.as_traitkey(item)

        tk = self.trait_mapping.update_trait_key_with_defaults(tk)
        trait = self.trait_class(sample=self.sample, trait_key=tk,
                                 astro_object=self.astro_object,
                                 trait_registry=self.trait_mapping,
                                 trait_schema=self.trait_mapping.trait_schema)

        # @TODO: Object Caching?

        return trait


# ___  __         ___                __   __          __      __   __
#  |  |__)  /\  |  |      |\/|  /\  |__) |__) | |\ | / _`    |  \ |__)
#  |  |  \ /~~\ |  |      |  | /~~\ |    |    | | \| \__>    |__/ |__)
#

class TraitMappingDatabase(bases.TraitMappingDatabase):
    """Trait Registries handle mappings of Trait Paths to columns.

    An archive module can define Traits and TraitCollections, which are then registered
    against a TraitRegistry. The TraitRegistry will introspect the trait classes provided
    in order to build up the schema.

    As part of the introspection, the registry will also validate that each Trait's slots
    have been correctly filled (e.g. with another trait or a column of a particular type).

    The TraitRegistry keeps a list of all valid TraitPaths that it knows about.

    ???
    As part of registration, the Registry will update each TraitClass with information about
    where it appears in the hierarchy.

    ???
    It also handles instanciating traits as required when they are looked up

    When Traits are instanciated, they are provided with the trait key used to instanciate
    them, the archive instance containing them, and the trait path leading to them.

    """

    def __init__(self):
        self.mappings = dict()  # type: Dict[Tuple[str, str], fidia.traits.TraitMapping]
        self.linked_mappings = []  # type: List[TraitMappingDatabase]

    def link_database(self, other_database, index=-1):
        # type: (TraitMappingDatabase, int) -> None
        assert isinstance(other_database, TraitMappingDatabase)
        self.linked_mappings.insert(index, other_database)

    def register_trait_mapping(self, trait_mapping):
        # type: (fidia.traits.TraitMapping) -> None
        if trait_mapping.key() in self.mappings:
            raise FIDIAException("Attempt to add an existing mapping")
        trait_mapping.validate()
        self.mappings[trait_mapping.key()] = trait_mapping

    def register_trait_mapping_list(self, trait_mapping_list):
        # type: (List[fidia.traits.TraitMapping]) -> None

        for mapping in trait_mapping_list:
            self.register_trait_mapping(mapping)

    def get_trait_mappings(self):

        # @TODO: This raises an exception if there are duplicate TraitMapping entries in the system.

        trait_mapping_keys_returned = set()

        for tm in self.mappings.values():
            string_key = "-".join(tm.key())
            if string_key in trait_mapping_keys_returned:
                raise FIDIAException('Duplicate TraitMappings found: %s' % string_key)
            trait_mapping_keys_returned.add(string_key)
            yield tm

        for sub_database in self.linked_mappings:
            for tm in sub_database.mappings.values():
                string_key = "-".join(tm.key())
                if string_key in trait_mapping_keys_returned:
                    raise FIDIAException('Duplicate TraitMappings found: %s' % string_key)
                yield tm


class MappingBase:
    
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

    def key(self):
        return self.trait_class.__name__, str(self.trait_key)

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


class TraitMapping(MappingBase):

    def __init__(self, trait_class, trait_key, schema, branches_versions=None, branch_version_defaults=None):
        # type: (Type[fidia.Trait], str, List[Union[TraitMapping, TraitPropertyMapping, SubTraitMapping]]) -> None
        
        super(TraitMapping, self).__init__(branches_versions, branch_version_defaults)
        
        assert issubclass(trait_class, fidia.traits.BaseTrait)
        self.trait_class = trait_class
        self.trait_key = TraitKey.as_traitkey(trait_key)
        self.trait_schema = schema


    def __repr__(self):
        return ("TraitMapping(trait_class=%s, trait_key='%s', schema=%s" %
                (self.trait_class.__name__, str(self.trait_key), str(self.trait_schema)))


    def validate(self):
        # Check that all required (not optional) TraitProperties are defined in the schema:
        for tp in self.trait_class._trait_properties():
            if tp.name not in self.trait_schema and not tp.optional:
                raise TraitValidationError("Trait %s missing required TraitProperty %s in definition" % (self, tp.name))

class TraitCollectionMapping(MappingBase):
    def __init__(self, trait_class, trait_key, schema, branches_versions=None, branch_version_defaults=None):
        # type: (Type[fidia.Trait], str, List[Union[TraitMapping, TraitPropertyMapping, SubTraitMapping]]) -> None
        assert issubclass(trait_class, fidia.traits.BaseTrait)
        self.trait_class = trait_class
        self.trait_key = TraitKey.as_traitkey(trait_key)
        self.trait_schema = schema

        self.branches_versions = self._init_branches_versions(branches_versions)
        self._branch_version_defaults = self._init_default_branches_versions(branch_version_defaults)

class SubTraitMapping(MappingBase):
    def __init__(self, sub_trait_name, trait_class, schema):
        # type: (str, Type[fidia.Trait], List[Union[TraitMapping, TraitPropertyMapping, SubTraitMapping]]) -> None
        assert issubclass(trait_class, fidia.traits.BaseTrait)
        self.trait_class = trait_class
        self.name = sub_trait_name
        self.trait_schema = schema


class TraitPropertyMapping:
    def __init__(self, property_name, column_id):
        # type: (str, str) -> None
        self.name = property_name
        self.id = column_id
