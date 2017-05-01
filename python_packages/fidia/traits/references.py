from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import Type, Dict
# import fidia

# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports
import fidia.base_classes as bases
from fidia.exceptions import *
from fidia.traits.trait_key import TraitKey, BranchesVersions, DefaultsRegistry, \
    validate_trait_branch, validate_trait_version
# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['TraitMapping', 'TraitPointer']

class ColumnReference(object):

    def __init__(self, column_id_or_alias):
        if column_id_or_alias is None:
            raise FIDIAException("a column reference must provide either a column id or an alias.")
        self.column_id_or_alias = column_id_or_alias
        self.column_id = None

    def is_resolved(self):
        return self.column_id is not None


class TraitMapping(bases.TraitMapping):

    def __init__(self, trait_class, trait_key, schema, branches_versions=None, branch_version_defaults=None):
        # type: (Type[fidia.Trait], str, Dict[str, Union[str, TraitMapping]]) -> None
        # assert issubclass(fidia.traits.BaseTrait, trait_class)
        self.trait_class = trait_class
        self.trait_key = TraitKey.as_traitkey(trait_key)
        self.trait_schema = schema

        self.branches_versions = self._init_branches_versions(branches_versions)
        self._branch_version_defaults = self._init_default_branches_versions(branch_version_defaults)

    def _init_branches_versions(self, branches_versions):
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
        """"""
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

    def __repr__(self):
        return ("TraitMapping(trait_class=%s, trait_key='%s', schema=%s" %
                (self.trait_class.__name__, str(self.trait_key), str(self.trait_schema)))

    def key(self):
        return self.trait_class, self.trait_key

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
        # type: (fidia.Sample, fidia.AstronomicalObject, TraitMapping, fidia.traits.TraitRegistry) -> None
        self.sample = sample
        self.astro_object = astro_object
        self.trait_mapping = trait_mapping
        self.trait_registry = trait_registry
        self.trait_class = trait_mapping.trait_class
        assert issubclass(fidia.traits.BaseTrait, self.trait_class)



    def __getitem__(self, item):
        tk = TraitKey.as_traitkey(item)

        tk = self.trait_mapping.update_trait_key_with_defaults(tk)
        trait = self.trait_class(sample=self.sample, trait_key=tk,
                                 object_id=self.astro_object.identifier,
                                 trait_registry=self.trait_mapping,
                                 trait_schema=self.trait_mapping.trait_schema)

        # @TODO: Object Caching?

        return trait
