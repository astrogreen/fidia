from itertools import product
from .utilities import TraitKey, validate_trait_name, validate_trait_type
from ..utilities import SchemaDictionary, DefaultsRegistry, Inherit

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

class TraitRegistry:

    def __init__(self):
        self._registry = set()
        self._trait_lookup = dict()
        self._trait_name_defaults = dict()

    def register(self, trait):
        log.debug("Registering Trait '%s'", trait)

        # Confirm that the supplied Trait has all required attributes
        trait._validate_trait_class()

        # Add the trait to the set of known trait classes in this registry.
        self._registry.add(trait)

        # Determine available qualifiers:
        if trait.qualifiers is not None:
            qualifiers = trait.qualifiers
        else:
            qualifiers = {None}

        # Determine available branches:
        if trait.branches_versions is None:
            branches = {None: [None]}
        else:
            branches = trait.branches_versions

        # Generate all possible trait keys, and map them all to this trait.
        # log.vdebug("Qualifiers: %s", qualifiers)
        # log.vdebug("Branches: %s", branches),
        # log.vdebug("Versions: %s", versions)
        for qualifier, branch in product(qualifiers, branches):
            for version in branches[branch]:
                tk = TraitKey(trait.trait_type, qualifier, branch, version)
                if tk in self._trait_lookup:
                    # @TODO: Raising this will leave the registry in a strange state.
                    raise ValueError("Attempt to redefine Trait belonging to TraitKey '%s'", tk)
                log.debug("Registering '%s' -> '%s'", tk, trait)
                self._trait_lookup[tk] = trait

        # Generate all possible trait_names
        for qualifier in qualifiers:
            trait_name = TraitKey.as_trait_name(trait.trait_type, qualifier)
            if trait_name not in self._trait_name_defaults:
                self._trait_name_defaults[trait_name] = DefaultsRegistry()
            if hasattr(trait, 'defaults'):
                self._trait_name_defaults[trait_name].update_defaults(trait.defaults)


        return trait

    def update_key_with_defaults(self, trait_key):
        """Return TraitKey with branch and version populated from defaults.

        Check the provided trait key, and if either the branch or version
        have not been provided (none), then return an updated version.

        """
        # Ensure we are working with a full TraitKey object (or convert if necessary)
        tk = TraitKey.as_traitkey(trait_key)

        # If the branch has not been specified, get the default from the DefaultsRegistry for this trait_name
        if tk.branch is None:
            tk = tk.replace(branch=self._trait_name_defaults[tk.trait_name].branch)
            log.debug("Branch not supplied for '%s', using default '%s'", tk.trait_name, tk.branch)

        # If the version has not been specified, get the default from the DefaultsRegistry for this trait_name
        if tk.version is None:
            tk = tk.replace(version=self._trait_name_defaults[tk.trait_name].version(tk.branch))
            log.debug("Version not supplied for '%s', using default '%s'", tk.trait_name, tk.version)

        return tk

    def retrieve_with_key(self, trait_key):
        # Ensure we are working with a full TraitKey object (or convert if necessary)
        tk = TraitKey.as_traitkey(trait_key)
        log.debug("Retrieving trait for key %s", tk)
        return self._trait_lookup[tk]

    # def retrieve_with_key_with_wildcards(self, trait_key):
    #     pass

    # def __getitem__(self, trait_key):
    #     return self.retrieve_with_key(trait_key)

    def get_traits(self, trait_type_filter=None, trait_name_filter=None):
        """Return a list of all Trait classes, optionally filtering for a particular trait_type."""

        if trait_type_filter is not None and trait_name_filter is not None:
            log.error("Trait Registry %s asked to filter both on trait_type and trait_name (not possible.)", self)
            raise ValueError("Only one of trait_type_filter and trait_name_filter can be defined.")
        if trait_type_filter is not None:
            validate_trait_type(trait_type_filter)
            log.debug("Filtering for traits with trait_type '%s'", trait_type_filter)
            result = []
            for trait in self._registry:
                if trait.trait_type == trait_type_filter:
                    result.append(trait)
            return result
        elif trait_name_filter is not None:
            validate_trait_name(trait_name_filter)
            log.debug("Filtering for traits with trait_name '%s'", trait_name_filter)
            result = []
            for trait in self._registry:
                log.debug("    Considering trait with name '%s'", trait.trait_name)
                # if trait.trait_name == trait_name_filter:
                if trait.answers_to_trait_name(trait_name_filter):
                    result.append(trait)
            return result
        else:
            # No filter applied. Return all classes.
            log.debug("Returning all traits of this TraitRegistry (no filter applied).")
            return self._registry

    def get_all_traitkeys(self):
        """A list of all known trait keys in the registry."""
        return self._trait_lookup.keys()

    def get_trait_names(self):
        """A list of the unique trait types in this TraitRegistry."""
        return self._trait_name_defaults.keys()

