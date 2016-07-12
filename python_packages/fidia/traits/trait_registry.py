from itertools import product
from .utilities import TraitKey

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

class TraitRegistry:

    def __init__(self):
        self._registry = set()
        self._trait_lookup = dict()
        self._all_trait_names = set()

    def register(self, trait):
        log.debug("Registering Trait '%s'", trait)

        # Confirm that the supplied Trait has all required attributes
        assert hasattr(trait, 'trait_type'), "Trait must have 'trait_type' attribute."
        if trait.qualifier_required:
            assert hasattr(trait, 'qualifiers'), "Trait must have 'qualifiers' attribute."

        # Add the trait to the set of known trait classes in this registry.
        self._registry.add(trait)

        # Determine available branches:
        if hasattr(trait, 'available_branches'):
            branches = trait.available_branches
        else:
            branches = {None}

        # Determine available versions:
        if hasattr(trait, 'available_versions'):
            versions = trait.available_versions
        else:
            versions = {None}

        # Determine available qualifiers:
        if trait.qualifier_required:
            qualifiers = trait.qualifiers
        else:
            qualifiers = {None}

        # Generate all possible trait keys, and map them all to this trait.
        # log.vdebug("Qualifiers: %s", qualifiers)
        # log.vdebug("Branches: %s", branches),
        # log.vdebug("Versions: %s", versions)
        for qualifier, branch, version in product(qualifiers, branches, versions):

            tk = TraitKey(trait.trait_type, qualifier, branch, version)
            if tk in self._trait_lookup:
                # @TODO: Raising this will leave the registry in a strange state.
                raise ValueError("Attempt to redefine Trait belonging to TraitKey '%s'", tk)
            log.debug("Registering '%s' -> '%s'", tk, trait)
            self._trait_lookup[tk] = trait

        # Generate all possible trait names and map them to this trait.
        for qualifier in qualifiers:
            trait_name = TraitKey.as_trait_name(trait.trait_type, qualifier)
            self._all_trait_names.add(trait_name)

        return trait

    def retrieve_with_key(self, trait_key):
        tk = TraitKey.as_traitkey(trait_key)
        return self._trait_lookup[tk]

    # def retrieve_with_key_with_wildcards(self, trait_key):
    #     pass

    # def __getitem__(self, trait_key):
    #     return self.retrieve_with_key(trait_key)

    def get_traits(self, trait_type_filter=None, trait_name_filter=None):
        """Return a list of all Trait classes, optionally filtering for a particular trait_type."""

        if trait_type_filter is not None and trait_name_filter is not None:
            raise ValueError("Only one of trait_type_filter and trait_name_filter can be defined.")
        if trait_type_filter is None:
            return self._registry
        elif trait_type_filter is not None:
            result = []
            for trait in self._registry:
                if trait.trait_type == trait_type_filter:
                    result.append(trait)
            return result
        elif trait_name_filter is not None:
            result = []
            for trait in self._registry:
                if trait.trait_name == trait_name_filter:
                    result.append(trait)
            return result

    def get_all_traitkeys(self):
        """A list of all known trait keys in the registry."""
        return self._trait_lookup.keys()

    def get_trait_names(self):
        """A list of the unique trait types in this TraitRegistry."""
        return self._all_trait_names

