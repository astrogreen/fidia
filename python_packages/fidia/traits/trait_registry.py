"""
Trait Registries handle mappings of Trait Paths to columns.

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

from __future__ import absolute_import, division, print_function, unicode_literals

if None:
    # These imports are purely for linting and code correctness checking
    from typing import Dict, List, Type, Union, Tuple
    import fidia

# Python Standard Library Imports
from itertools import product

# Other Library Imports

# FIDIA Imports
from fidia.exceptions import *
from .trait_key import TraitKey, validate_trait_name
from ..fidiatype import fidia_type
from ..utilities import DefaultsRegistry, SchemaDictionary, is_list_or_set
from .. import exceptions

# Logging import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

class TraitRegistry:

    def __init__(self, branches_versions_required=False):
        self._registry = set()
        self._trait_lookup = dict()
        self._trait_name_defaults = dict()  # type: Dict[str, DefaultsRegistry]
        self.branches_versions_required = branches_versions_required

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
            if self.branches_versions_required:
                raise exceptions.TraitValidationError(
                    "The Trait '%s' ('%s') must define at least one branch and one version." %
                    (trait.__name__, trait.trait_type))
            else:
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
                    raise ValueError("Attempt to redefine Trait belonging to TraitKey '%s'" % str(tk))
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

    def change_defaults(self, trait_name, new_defaults):
        log.debug("Updating trait branch and version defaults for '%s'" % trait_name)
        self._trait_name_defaults[trait_name].update_defaults(new_defaults)
        log.debug("New defaults: %s" % str(self._trait_name_defaults[trait_name]))

    def update_key_with_defaults(self, trait_key):
        """Return TraitKey with branch and version populated from defaults.

        Check the provided trait key, and if either the branch or version
        have not been provided (none), then return an updated version based on
        the contents of the defaults registry (if possible)

        """
        # Ensure we are working with a full TraitKey object (or convert if necessary)
        tk = TraitKey.as_traitkey(trait_key)

        log.debug("Updating TraitKey '%s' with defaults" % str(trait_key))

        if tk.trait_name not in self._trait_name_defaults:
            # No defaults information for this trait_name, so nothing we can do.
            log.warn("No Defaults information for TraitKey '%s' in registry.", tk)
            return tk

        # If the branch has not been specified, get the default from the DefaultsRegistry for this trait_name
        if tk.branch is None:
            tk = tk.replace(branch=self._trait_name_defaults[tk.trait_name].branch)
            log.debug("Branch not supplied for '%s', using default '%s'", tk.trait_name, tk.branch)

        # If the version has not been specified, get the default from the DefaultsRegistry for this trait_name
        if tk.version is None:
            # @TODO: Handle cases where this branch is not in the defaults registry.
            tk = tk.replace(version=self._trait_name_defaults[tk.trait_name].version(tk.branch))
            log.debug("Version not supplied for '%s', using default '%s'", tk.trait_name, tk.version)

        return tk

    def retrieve_with_key(self, trait_key):
        # type: (TraitKey) -> Trait
        # Ensure we are working with a full TraitKey object (or convert if necessary)
        tk = TraitKey.as_traitkey(trait_key)
        log.debug("Retrieving trait for key %s", tk)
        return self._trait_lookup[tk]

    # def retrieve_with_key_with_wildcards(self, trait_key):
    #     pass

    # def __getitem__(self, trait_key):
    #     return self.retrieve_with_key(trait_key)

    def get_trait_classes(self, trait_type_filter=None, trait_name_filter=None):
        # type: (str, str) -> List[Trait]
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

    def get_all_traitkeys(self, trait_type_filter=None, trait_name_filter=None):
        # type: (str, str) -> List[TraitKey]
        """A list of all known trait keys in the registry, optionally filtered."""
        filtered_keys = set()
        all_keys = self._trait_lookup.keys()

        # Note that the trait name filter is more specific, so if present, it is
        # run first (and then there is no need to do a trait type filter).
        if trait_name_filter is not None:
            # Then filter for matching trait names
            for trait_key in all_keys:
                if trait_key.trait_name == trait_name_filter:
                    filtered_keys.add(trait_key)
        elif trait_type_filter is not None:
            # Then filter for matching trait types
            for trait_key in all_keys:
                if trait_key.trait_type == trait_type_filter:
                    filtered_keys.add(trait_key)
        else:
            filtered_keys = all_keys
        return filtered_keys

    def get_trait_types(self):
        # type: () -> Set[str]
        return {t.trait_type for t in self.get_trait_classes()}

    def get_trait_names(self, trait_type_filter=None):
        # type: (str) -> Set[str]
        """A list of the unique trait names in this TraitRegistry, optionally filtered.

        trait_type_filter: (string) trait_type to get names for.

        """
        filtered_names = set()
        all_names = self._trait_name_defaults.keys()

        if trait_type_filter is not None:
            # Then filter for matching trait types
            for trait_name in all_names:
                if TraitKey.split_trait_name(trait_name)[0] == trait_type_filter:
                    filtered_names.add(trait_name)
            return filtered_names
        else:
            return all_names


    def schema(self, include_subtraits=True, data_class='all', combine_levels=None, verbosity='data_only',
               separate_metadata=False):
        """Construct the schema for all Trait classes registered.

        The schema is constructed by calling the `schema` function on the class
        responding to each TraitKey registered.

        IMPLEMENTATION NOTE: Multiple TraitKeys can and often do point to the
        same class. Currently, the schema function is called for every TraitKey,
        regardless of whether it has already been called on that class. In
        theory, this unnecessary repetition of the schema call could be
        eliminated.

        """

        if combine_levels is None:
            combine_levels = tuple()

        for item in combine_levels:
            assert item in ('trait_name', 'branch_version', 'no_trait_qualifier')

        schema = SchemaDictionary()

        def add_description_data_for_levels(other_dictionary, trait_key,
                                            levels=['trait_type', 'trait_qualifier', 'branch_version']):
            # type: (SchemaDictionary, List[str]) -> None
            """Helper function to populate description data for the given levels."""

            # Do nothing if descriptions not requested.
            if verbosity != 'descriptions':
                return

            # Validate input
            if not is_list_or_set(levels):
                levels = [levels]
            for item in levels:
                assert item in ('trait_type', 'trait_qualifier', 'branch_version'), "%s is not a valid level." % item

            trait = self.retrieve_with_key(tk)  # type: Trait

            if 'trait_type' in levels:
                other_dictionary['pretty_name-trait_type'] = trait.get_pretty_name()
            if 'trait_qualifier' in levels:
                if trait_key.trait_qualifier is not None:
                    other_dictionary['pretty_name-trait_qualifier'] = trait.get_qualifier_pretty_name(
                        trait_key.trait_qualifier)
                other_dictionary['pretty_name-trait_name'] = trait.get_pretty_name(trait_key.trait_qualifier)

            # Add a generic 'pretty_name'
            #
            #   - At the trait_type level, this is just the pretty version of the trait_type
            #   - At the trait_qualifier level, this is just the pretty version of qualifier
            #   - When type and qualifier are combined, this is the pretty version of the full trait_name
            #
            if separate_metadata:
                # if branch and version are combined, then the pretty_name set here will clash with that set for the
                # individual trait schema, so we skip this version.
                if 'trait_type' in levels and 'trait_qualifier' in levels:
                    # Set the pretty version of the full trait_name (type and qualifier)
                    other_dictionary['pretty_name'] = trait.get_pretty_name(trait_key.trait_qualifier)
                elif 'trait_type' in levels:
                    # Set the pretty version of just the trait_type
                    other_dictionary['pretty_name'] = trait.get_pretty_name()
                elif 'trait_qualifier' in levels:
                    # set the pretty version of just the trait_qualifier, or empty string if no qualifier.
                    if trait_key.trait_qualifier is not None:
                        other_dictionary['pretty_name'] = trait.get_qualifier_pretty_name(trait_key.trait_qualifier)
                    else:
                        other_dictionary['pretty_name'] = ""

                if 'trait_type' in levels:
                    # Add Generic Trait Descriptions
                    fidia_trait_class = fidia_type(trait)
                    other_dictionary['description'] = fidia_trait_class.get_description()


        def add_default_branch_to_schema(trait_key, schema_piece):
            """If descriptions are requested, add the default branch of this Trait."""
            # TODO: Checking for 'branch_version' is not an authoritative way to determine sub-traits.
            if verbosity != 'descriptions' or 'branch_version' in combine_levels:
                return
            schema_piece['default_branch'] = self._trait_name_defaults[trait_key.trait_name].branch

        def add_default_version_to_schema(trait_key, schema_piece):
            """If descriptions are requested, add the default version of this Trait for the current branch."""
            # TODO: Checking for 'branch_version' is not an authoritative way to determine sub-traits.
            if verbosity != 'descriptions' or 'branch_version' in combine_levels:
                return
            schema_piece['default_version'] = self._trait_name_defaults[trait_key.trait_name].version(trait_key.branch)

        def add_branch_description_to_schema(trait_key, trait_class, schema_piece):
            if verbosity != 'descriptions':
                return
            if 'branch_version' in combine_levels:
                # Multiple brances and versions on this level, so cannot add
                # description for a particular branch
                return
            if trait_class.branches_versions is None:
                # No branches or versions defined
                # @TODO: Force branches and versions to be defined?
                schema_piece['pretty_name'] = "None"
                schema_piece['description'] = ""
                return
            schema_piece['pretty_name'] = trait_class.branches_versions.get_pretty_name(trait_key.branch)
            schema_piece['description'] = trait_class.branches_versions.get_description(trait_key.branch)

        def add_version_description_to_schema(trait_key, trait_class, schema_piece):
            if verbosity != 'descriptions':
                return
            if 'branch_version' in combine_levels:
                # Multiple brances and versions on this level, so cannot add
                # description for a particular branch
                return
            if trait_class.branches_versions is None:
                # No branches or versions defined
                # @TODO: Force branches and versions to be defined?
                schema_piece['pretty_name'] = "None"
                schema_piece['description'] = ""
                return
            schema_piece['pretty_name'] = trait_class.branches_versions.get_version_pretty_name(
                trait_key.branch, trait_key.version)
            schema_piece['description'] = trait_class.branches_versions.get_version_description(
                trait_key.branch, trait_key.version)


        def get_schema_element(trait_key, trait_class):
            # type: (TraitKey) -> SchemaDictionary
            """A helper function that finds the appropriate schema element given the requests to combine levels.

            This dramatically reduces the complexity of this part of the code.
            Previously, there were different if/else branches for each option,
            and lots of almost repetition.

            Basically, depending on what "combine"ing of levels has been
            requested, this creates all the necessary intervening levels of the
            schema dictionary, and then return a pointer to the actual Schema
            Dictionary that needs to have the schema data from the Trait added.

            Additionally, if descriptions are requested, then it inserts all
            relevant pretty names at each level (regardless of whether they are
            combined or not).

            """

            if 'trait_name' in combine_levels:
                piece = schema.setdefault(trait_key.trait_name, SchemaDictionary())
                add_description_data_for_levels(piece, trait_key, ['trait_type', 'trait_qualifier'])
                if separate_metadata:
                    # Add an additional level to separate metadata from schema
                    piece = piece.setdefault('trait_names', SchemaDictionary())

            elif 'no_trait_qualifier' in combine_levels:
                # For traits that do not support a trait qualifier, then don't
                # add a level to the schema for the trait qualifier.
                if trait_key.trait_qualifier is None:
                    # Qualifiers not present: behave as for 'trait_name'
                    piece = schema.setdefault(trait_key.trait_name, SchemaDictionary())
                    add_description_data_for_levels(piece, trait_key, ['trait_type', 'trait_qualifier'])
                    if separate_metadata:
                        # Add an additional level to separate metadata from schema
                        piece = piece.setdefault('trait_names', SchemaDictionary())
                else:
                    # Qualifiers present: behave as if 'trait_name' was not given
                    piece = schema.setdefault(trait_key.trait_type, SchemaDictionary())
                    add_description_data_for_levels(piece, trait_key, ['trait_type'])
                    piece = piece.setdefault(trait_key.trait_qualifier, SchemaDictionary())
                    add_description_data_for_levels(piece, trait_key, ['trait_qualifier'])

            else:
                # Do not combine trait_type and trait_qualifier into trait_name
                piece = schema.setdefault(trait_key.trait_type, SchemaDictionary())
                add_description_data_for_levels(piece, trait_key, ['trait_type'])

                if separate_metadata:
                    # Add an additional level to separate metadata from schema
                    piece = piece.setdefault('trait_qualifiers', SchemaDictionary())
                piece = piece.setdefault(trait_key.trait_qualifier, SchemaDictionary())
                add_description_data_for_levels(piece, trait_key, ['trait_qualifier'])

            if 'branch_version' in combine_levels:
                # If branch and version are combined, then the version data will
                # be overwritten. Lines below commented out. NOTE ALSO: branches
                # and versions not relevant for sub-traits.

                # add_default_branch_to_schema(trait_key, piece)
                # add_default_version_to_schema(trait_key, piece)
                pass
            else:
                add_default_branch_to_schema(trait_key, piece)

                if separate_metadata:
                    # Add an additional level to separate metadata from schema
                    piece = piece.setdefault('branches', SchemaDictionary())
                piece = piece.setdefault(trait_key.branch, SchemaDictionary())
                add_branch_description_to_schema(trait_key, trait_class, piece)

                add_default_version_to_schema(trait_key, piece)
                if separate_metadata:
                    # Add an additional level to separate metadata from schema
                    piece = piece.setdefault('versions', SchemaDictionary())
                piece = piece.setdefault(trait_key.version, SchemaDictionary())
                add_version_description_to_schema(trait_key, trait_class, piece)

                # Add the information on the default branch and version information

            if separate_metadata:
                # Add an additional level to separate metadata from schema
                piece = piece.setdefault('trait', SchemaDictionary())

            return piece

        for tk in self.get_all_traitkeys():
            trait_class = self.retrieve_with_key(tk)  # type: Trait
            piece = get_schema_element(tk, trait_class)
            trait_schema = trait_class.full_schema(
                include_subtraits=include_subtraits,
                data_class=data_class,
                combine_levels=combine_levels,
                verbosity=verbosity,
                separate_metadata=separate_metadata)
            piece.update(trait_schema)

        if data_class != 'all':
            # Check for empty Trait schemas and remove (only necessary if there
            # has been filtering on catalog/non-catalog data)
            schema.delete_empty()

            # Handle filtering of verbosities other than 'data-only'
            if verbosity != 'data_only':
                filter_schema = self.schema(include_subtraits=True, data_class=data_class, combine_levels=[],
                                            verbosity='data_only', separate_metadata=False)
                keys_to_delete = []
                for key in schema:
                    if key not in filter_schema.keys():
                        keys_to_delete.append(key)

                while len(keys_to_delete) > 0:
                    key = keys_to_delete.pop()
                    del schema[key]

        return schema