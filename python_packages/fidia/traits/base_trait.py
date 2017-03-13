from __future__ import absolute_import, division, print_function, unicode_literals

# Standard Library Imports
import pickle
from io import BytesIO
from collections import OrderedDict, Mapping
import re


# Other library imports
from astropy.io import fits

# Internal package imports
from .abstract_base_traits import *
from ..exceptions import *
from .trait_property import TraitProperty
from .trait_key import TraitKey, TraitPath, TRAIT_NAME_RE, \
    validate_trait_type, validate_trait_qualifier, validate_trait_version, validate_trait_branch, \
    BranchesVersions
from .trait_registry import TraitRegistry
from ..utilities import SchemaDictionary, is_list_or_set, DefaultsRegistry, RegexpGroup
from ..descriptions import TraitDescriptionsMixin, DescriptionsMixin

# This makes available all of the usual parts of this package for use here.
#
# I think this will not cause a circular import because it is a module level import.
# from . import meta_data_traits

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


# class DictTrait(Mapping):
#     """A "mix-in class which provides dict-like access for Traits
#
#     Requires that the class mixed into implements a `_trait_dict` cache
#
#     """
#
#     def __iter__(self):
#         pass
#     def __getitem__(self, item):
#         if item in self._trait_cache:
#             return self._trait_cache[item]
#         else:
#             return getattr(self, item)
#
#     def __len__(self):
#         return 0

def validate_trait_branches_versions_dict(branches_versions):
    # type: ([BranchesVersions, None]) -> None
    if branches_versions is None:
        return
    assert isinstance(branches_versions, dict), "`branches_versions` must be a dictionary"
    # Check that all branches meet the branch formatting requirements
    for branch in branches_versions:
        if branch is not None:
            validate_trait_branch(branch)
        # Check that each branch has a list of versions:
        assert is_list_or_set(branches_versions[branch])
        # Check that all versions meet the branch formatting requirements
        for version in branches_versions[branch]:
            if version is not None:
                validate_trait_version(version)


class BaseTrait(TraitDescriptionsMixin, AbstractBaseTrait):

    # The following are a required part of the Trait interface.
    # They must be set in sub-classes to avoid an error trying create a Trait.
    trait_type = None
    qualifiers = None
    branches_versions = None

    descriptions_allowed = 'class'

    #             ___               __                       __       ___    __
    #    | |\ | |  |      /\  |\ | |  \    \  /  /\  |    | |  \  /\   |  | /  \ |\ |
    #    | | \| |  |     /~~\ | \| |__/     \/  /~~\ |___ | |__/ /~~\  |  | \__/ | \|
    #

    def __init__(self, archive, trait_key=None, object_id=None, parent_trait=None):
        super().__init__()

        self._validate_trait_class()

        self.archive = archive
        self._parent_trait = parent_trait

        assert isinstance(trait_key, TraitKey), "In creation of Trait, trait_key must be a TraitKey, got %s" % trait_key
        self.trait_key = trait_key

        self._set_branch_and_version(trait_key)

        if object_id is None:
            raise KeyError("object_id must be supplied")
        self.object_id = object_id
        self.trait_qualifier = trait_key.trait_qualifier

        self._trait_cache = OrderedDict()

        if parent_trait is not None:
            self.trait_path = TraitPath(parent_trait.trait_path + (self.trait_key, ))
        else:
            self.trait_path = TraitPath([self.trait_key])

    def _post_init(self):
        pass

    @classmethod
    def _validate_trait_class(cls):
        assert cls.trait_type is not None, "trait_type must be defined"
        validate_trait_type(cls.trait_type)

        assert cls.qualifiers is None or is_list_or_set(cls.qualifiers), "qualifiers must be a list or set or None"
        if cls.qualifiers is not None:
            for qual in cls.qualifiers:
                validate_trait_qualifier(qual)
        # assert cls.available_versions is not None

        if cls.branches_versions is not None:
            if not isinstance(cls.branches_versions, BranchesVersions):
                cls.branches_versions = BranchesVersions(cls.branches_versions)
            if getattr(cls, 'defaults', None) is None:
                # Defaults not provided. See if only one branch/version are supplied
                if cls.branches_versions.has_single_branch_and_version():
                    # Set the defaults to be the only branch/version:
                    cls.defaults = cls.branches_versions.as_defaults()  # type: DefaultsRegistry
                    log.debug(cls.defaults._default_branch)
                    log.debug(cls.defaults._version_defaults)
                else:
                    raise Exception("Trait class '%s' has branches_versions, but no defaults have been supplied." %
                            cls)

        try:
            validate_trait_branches_versions_dict(cls.branches_versions)
        except AssertionError as e:
            raise TraitValidationError(e.args[0] + " on trait class '%s'" % cls)

    def _set_branch_and_version(self, trait_key):
        """Trait Branch and Version handling:

        The goal of this is to set the trait branch and version if at all possible. The
        following are tried:
        - If version explicitly provided in this initialisation, that is the version.
        - If this is a sub trait check the parent trait for it's version.
        - If the version is still none, try to set it to the default for this trait.
        """

        # if log.isEnabledFor(slogging.DEBUG):
        assert isinstance(trait_key, TraitKey)

        def validate_and_inherit(trait_key, parent_trait, valid, attribute):
            """Helper function to validate and/or inherit.

            This is defined because the logic is identical for both branches
            and versions, so this avoides repetition

            """

            current_value = getattr(trait_key, attribute)

            if current_value is not None:
                # We have been given a (branch/version) value, check that it
                # is valid for this Trait:
                if valid is not None:
                    assert current_value in valid, \
                        "%s '%s' not valid for trait '%s'" % (attribute, current_value, self)
                return current_value
            elif current_value is None:
                # We have been asked to inherit the branch/version from the
                # parent trait. If the parent_trait is defined (i.e. this is
                # not a top level trait), then take its value if it is valid
                # for this trait.
                if parent_trait is not None:
                    parent_value = getattr(parent_trait, attribute)
                    # This is a sub trait. Inherit branch from parent unless not valid.
                    if valid is None:
                        # All options are valid.
                        return parent_value
                    elif valid is not None and parent_value in valid:
                        return parent_value
                    else:
                        # Parent is not valid here, so leave as None
                        return None

        # Determine the branch given the options.
        self.branch = validate_and_inherit(trait_key, self._parent_trait, self.branches_versions, 'branch')

        # Now that the branch has been specified, determine the valid versions
        if self.branches_versions is not None:
            valid_versions = self.branches_versions[self.branch]
        else:
            valid_versions = None

        # Determine the version given the options
        self.version = validate_and_inherit(trait_key, self._parent_trait, valid_versions, 'version')

    #     __   __             __        ___  __                __           ___  __   __     __        __
    #    |__) |__)  /\  |\ | /  ` |__| |__  /__`     /\  |\ | |  \    \  / |__  |__) /__` | /  \ |\ | /__`
    #    |__) |  \ /~~\ | \| \__, |  | |___ .__/    /~~\ | \| |__/     \/  |___ |  \ .__/ | \__/ | \| .__/
    #

    @classmethod
    def answers_to_trait_name(cls, trait_name):
        match = TRAIT_NAME_RE.fullmatch(trait_name)
        if match is not None:
            log.debug("Checking if trait '%s' responds to trait_name '%s'", cls, trait_name)
            log.debug("TraitName match results: %s", match.groupdict())

            # Check the trait_name against all possible trait_names supported by this Trait.
            if match.group('trait_type') != cls.trait_type:
                return False

            # Confirm that the qualifier has been used correctly:
            if match.group('trait_qualifier') is not None and cls.qualifiers is None:
                raise ValueError("Trait type '%s' does not allow a qualifier." % cls.trait_type)
            if match.group('trait_qualifier') is None and cls.qualifiers is not None:
                raise ValueError("Trait type '%s' requires a qualifier." % cls.trait_type)

            # Check trait_name against all known qualifiers provided by this Trait.
            if cls.qualifiers is not None \
                    and match.group('trait_qualifier') not in cls.qualifiers:
                return False
            return True
        else:
            return False

    @property
    def trait_name(self):
        return self.trait_key.trait_name

    def get_all_branches_versions(self):
        # type: () -> Set[TraitKey]
        """Get all of the valid TraitKeys for Traits of this trait_name within the archive.

        This function effectively "spans" not only this particular class, but
        all other classes with the same trait_name in the current archive.

        Therefore, this is the preferred way to get the other branches and versions, rather than
        interrogating the value of `branches_versions`, which will not cover
        other classes with the same trait_name.

        """
        # NOTE: this must be an instance method because the parent_trait and
        # archive are not known by the class.

        if self._parent_trait is None:
            return self.archive.available_traits.get_all_traitkeys(trait_name_filter=self.trait_name)
        else:
            return self._parent_trait.sub_traits.get_all_traitkeys(trait_name_filter=self.trait_name)

    #
    #  __        __  ___  __         ___                    __               __
    # /__` |  | |__)  |  |__)  /\  |  |     |__|  /\  |\ | |  \ |    | |\ | / _`
    # .__/ \__/ |__)  |  |  \ /~~\ |  |     |  | /~~\ | \| |__/ |___ | | \| \__>

    sub_traits = TraitRegistry()

    def get_sub_trait(self, trait_key):
        """Retrieve a subtrait for the TraitKey.

        trait_key can be a TraitKey, or anything that can be interpreted as a TraitKey
        (using `TraitKey.as_traitkey`)

        """
        if trait_key is None:
            raise ValueError("The TraitKey must be provided.")
        trait_key = TraitKey.as_traitkey(trait_key)

        # Fill in default values for any `None`s in `TraitKey`
        trait_key = self.sub_traits.update_key_with_defaults(trait_key)

        # Check if we have already loaded this trait, otherwise load and cache it here.
        if trait_key not in self._trait_cache:

            # Check the size of the cache, and remove item if necessary
            # This should probably be more clever.
            while len(self._trait_cache) > 20:
                self._trait_cache.popitem(last=False)

            # Determine which class responds to the requested trait.
            # Potential for far more complex logic here in future.
            trait_class = self.sub_traits.retrieve_with_key(trait_key)

            # Create the trait object and cache it
            log.debug("Returning trait_class %s", type(trait_class))
            trait = trait_class(self.archive, trait_key, parent_trait=self, object_id=self.object_id)

            self._trait_cache[trait_key] = trait

        return self._trait_cache[trait_key]

    def get_all_subtraits(self, trait_type_filter=None):
        # type: (str, str) -> Trait
        """A generator which provides instantized subtraits of this Trait.

        This is distnct from the `TraitRegistry`s get_trait_classes, which will
        only return all of the classes, rather than actual Trait instances.

        Note that this explicitly does not consider the possibility of
        sub-traits having branches and versions (other than that of this trait).
        """

        # Version of this which would support sub-trait branches and versions:
        # for trait_key in self.sub_traits.get_all_traitkeys(trait_type_filter=trait_type_filter,
        #                                                    trait_name_filter=trait_name_filter):

        for trait_name in self.sub_traits.get_trait_names(trait_type_filter=trait_type_filter):
            trait = self.get_sub_trait(trait_name)
            yield trait



    #
    # ___  __         ___  __   __   __   __   ___  __  ___                        __               __
    #  |  |__)  /\  |  |  |__) |__) /  \ |__) |__  |__)  |  \ /    |__|  /\  |\ | |  \ |    | |\ | / _`
    #  |  |  \ /~~\ |  |  |    |  \ \__/ |    |___ |  \  |   |     |  | /~~\ | \| |__/ |___ | | \| \__>

    @classmethod
    def _trait_properties(cls, trait_property_types=None, include_hidden=False):
        """Generator which iterates over the TraitProperties attached to this Trait.

        :param trait_property_types:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        Note that the descriptor must be handed this Trait object to actually retrieve
        data, which is why this is implemented as a private method. See
        `trait_property_values` as a simpler alternative.

        Alternately, use the public `trait_properties` method to retrieve bound
        Trait Properties which do not have this complication (and see ASVO-425!)

        :returns: the TraitProperty descriptor object

        """

        if isinstance(trait_property_types, str):
            trait_property_types = tuple(trait_property_types)

        # Search class attributes:
        log.debug("Searching for TraitProperties of Trait '%s' with type in %s", cls.trait_type, trait_property_types)
        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, TraitProperty):
                if obj.name.startswith("_") and not include_hidden:
                    log.debug("Trait property '%s' ignored because it is hidden.", attr)
                    continue
                log.debug("Found trait property '{}' of type '{}'".format(attr, obj.type))
                if (trait_property_types is None) or (obj.type in trait_property_types):
                    yield obj

    @classmethod
    def trait_property_dir(cls):
        """Return a directory of TraitProperties for this object, similar to what the builtin `dir()` does."""
        for tp in cls._trait_properties():
            yield tp.name

    def trait_properties(self, trait_property_types=None, include_hidden=False):
        # type: (List, Bool) -> List[TraitProperty]
        """Generator which iterates over the (Bound)TraitProperties attached to this Trait.

        :param trait_property_types:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        :yields: a TraitProperty which is bound to this trait

        """

        # If necessary, convert a single trait property type argument to a list:
        if isinstance(trait_property_types, str):
            trait_property_types = tuple(trait_property_types)

        # Search class attributes. NOTE that this code is very similar to that
        # in `_trait_properties`. It has been reproduced here as
        # `_trait_properties` is probably going to be deprecated and removed if
        # ASVO-425 works out.
        #
        # Also note that, as written, this method avoids creating
        # BoundTraitProperty objects unless actually necessary.
        log.debug("Searching for TraitProperties of Trait '%s' with type in %s", self.trait_type, trait_property_types)
        cls = type(self)
        for attr in dir(cls):
            descriptor_obj = getattr(cls, attr)
            if isinstance(descriptor_obj, TraitProperty):
                if descriptor_obj.name.startswith("_") and not include_hidden:
                    log.debug("Trait property '%s' ignored because it is hidden.", attr)
                    continue
                log.debug("Found trait property '{}' of type '{}'".format(attr, descriptor_obj.type))
                if (trait_property_types is None) or (descriptor_obj.type in trait_property_types):
                    # Retrieve the attribute for this object (which will create
                    # the BoundTraitProperty: see `__get__` on `TraitProperty`)
                    yield getattr(self, attr)


    #     __   __        ___
    #    /__` /  ` |__| |__   |\/|  /\
    #    .__/ \__, |  | |___  |  | /~~\
    #

    @classmethod
    def schema(cls, include_subtraits=True, by_trait_name=False, data_class='all'):
        """Provide the schema of data in this trait as a dictionary.

        The schema is presented as a dictionary, where the keys are strings
        giving the name of the attributes defined, and the values are the FIDIA
        type strings for each attribute.

        Only attributes which are TraitProperties are included in the schema,
        unless `include_subtraits` is True.

        Examples:

            >>> galaxy['redshift'].schema()
            {'value': 'float', 'variance': 'float'}

        Parameters:

            include_subtraits:
                Recurse on any sub-traits attached to this Trait. The key will
                be the sub-trait name, and the value will be the schema
                dictionary describing the sub-trait.

            by_trait_name:
                Control how the sub-traits will be grouped. If True, then the
                key for a sub-Trait will be the sub_trait's full trait_name
                (trait_type + trait_qualifier), and the value will be the
                sub-Trait's schema.

                If False, then the key is the trait_type (only), and the value
                is a dictionary of trait_qualifiers (or the single key `None` if
                there are no qualifiers). This nested dictionary has values
                which are the sub-Trait's schema.

                See Archive.schema for an example of each.

            data_class:
                One of 'all', 'catalog', or 'non-catalog'

                'all' returns the full schema.

                'catalog' returns only items which contain TraitProperties of catalog type.

                'non-catalog' returns only items which contain TraitProperties of non-catalog type.

                Both 'catalog' and 'non-catalog' will not include Traits that
                consist only of TraitProperties not matching the request.

        """
        if by_trait_name:
            return cls.full_schema(include_subtraits=include_subtraits, data_class=data_class,
                                   combine_levels=['trait_name', 'branch_version'],
                                   separate_metadata=False, verbosity='simple')
        else:
            return cls.full_schema(include_subtraits=include_subtraits, data_class=data_class,
                                   combine_levels=['branch_version'],
                                   separate_metadata=False, verbosity='simple')


    @classmethod
    def full_schema(cls, include_subtraits=True, data_class='all', combine_levels=[], verbosity='data_only',
                    separate_metadata=False):

        log.debug("Creating schema for %s", str(cls))

        # Validate the verbosity option
        assert verbosity in ('simple', 'data_only', 'metadata', 'descriptions')
        if verbosity == 'descriptions':
            if 'branches_versions' in combine_levels:
                raise ValueError("Schema verbosity 'descriptions' requires that " +
                                 "combine_levels not include branches_versions")

        # Validate the data_class flag
        assert data_class in ('all', 'catalog', 'non-catalog', None)
        if data_class is None:
            data_class = 'all'

        # Create the empty schema for this Trait
        schema = SchemaDictionary()

        # Add basic metadata about this trait, if requested
        if verbosity in ('metadata', 'descriptions'):
            schema['trait_type'] = cls.trait_type
            # schema['branches_versions'] = cls.branches_versions

            # Available export formats (see ASVO-695)
            schema['export_formats'] = cls.get_available_export_formats()

            # Add unit information if present
            formatted_unit = cls.get_formatted_units()
            if formatted_unit:
                schema['unit'] = formatted_unit
            else:
                schema['unit'] = ""

        # Add description information for this trait to the schema if requested
        if verbosity == 'descriptions':
            cls.copy_descriptions_to_dictionary(schema)

        # Add TraitProperties of this Trait to the schema
        trait_properties_schema = SchemaDictionary()
        for trait_property in cls._trait_properties():
            if data_class == 'all' or \
                    (data_class == 'catalog' and trait_property.type in TraitProperty.catalog_types) or \
                    (data_class == 'non-catalog' and trait_property.type in TraitProperty.non_catalog_types):
                if verbosity == 'simple':
                    trait_property_schema = trait_property.type
                else:
                    # First get unit information
                    formatted_unit = trait_property.get_formatted_units()
                    if trait_property.name == 'value' and formatted_unit == '':
                        formatted_unit = cls.get_formatted_units()
                    trait_property_schema = SchemaDictionary(
                        type=trait_property.type,
                        name=trait_property.name,
                        unit=formatted_unit
                    )
                if verbosity == 'descriptions':
                    trait_property.copy_descriptions_to_dictionary(trait_property_schema)

                trait_properties_schema[trait_property.name] = trait_property_schema
        if verbosity == 'simple':
            schema.update(trait_properties_schema)
        else:
            schema['trait_properties'] = trait_properties_schema

        # Add sub-trait information to the schema.
        if include_subtraits:

            # Sub-traits cannot have branch/version information currently, so we
            # do not enumerate branches and versions in sub-traits.
            if 'branch_version' not in combine_levels:
                combine_levels += ('branch_version', )

            # Request the schema from the registry.
            sub_traits_schema = cls.sub_traits.schema(
                include_subtraits=include_subtraits,
                data_class=data_class,
                combine_levels=combine_levels,
                verbosity=verbosity,
                separate_metadata=separate_metadata)

            if verbosity == 'simple':
                schema.update(sub_traits_schema)
            else:
                schema['sub_traits'] = sub_traits_schema

        if data_class != 'all':
            # Check for empty Trait schemas and remove (only necessary if there
            # has been filtering on catalog/non-catalog data)
            schema.delete_empty()

        return schema



    #  __       ___          ___      __   __   __  ___           ___ ___       __   __   __
    # |  \  /\   |   /\     |__  \_/ |__) /  \ |__)  |      |\/| |__   |  |__| /  \ |  \ /__`
    # |__/ /~~\  |  /~~\    |___ / \ |    \__/ |  \  |      |  | |___  |  |  | \__/ |__/ .__/
    #
    # Note: Only data export methods which make sense for *any* trait are
    # defined here. Other export methods, such as FITS Export, are defined in
    # mixin classes.

    def as_pickled_bytes(self):
        """Return a representation of this TraitProperty as a serialized string of bytes"""
        dict_to_serialize = self._trait_dict
        with BytesIO() as byte_file:
            pickle.dump(dict_to_serialize, byte_file)
            return byte_file.getvalue()

    @classmethod
    def get_available_export_formats(cls):
        export_formats = []
        if hasattr(cls, 'as_fits'):
            export_formats.append("FITS")
        return export_formats

    #      ___          ___         ___            __  ___    __        __
    # |  |  |  | |    |  |  \ /    |__  |  | |\ | /  `  |  | /  \ |\ | /__`
    # \__/  |  | |___ |  |   |     |    \__/ | \| \__,  |  | \__/ | \| .__/
    #
    # Functions to augment behaviour in Python

    def __getitem__(self, key):
        # type: (TraitKey) -> Trait
        """Provide dictionary-like retrieve of sub-traits"""
        return self.get_sub_trait(key)

    def __str__(self):
        return "<Trait class '{classname}': {trait_type}>".format(classname=self.__class__.__name__, trait_type=self.trait_type)

    @classmethod
    def get_formatted_units(cls):
        if hasattr(cls, 'unit'):
            if hasattr(cls.unit, 'value'):
                formatted_unit = "{0.unit:latex_inline}".format(cls.unit)
                # formatted_unit = "{0.unit}".format(cls.unit)
            else:
                try:
                    formatted_unit = cls.unit.to_string('latex_inline')
                    # formatted_unit = cls.unit.to_string()
                except:
                    log.exception("Unit formatting failed for unit %s of trait %s, trying plain latex", cls.unit, cls)
                    try:
                        formatted_unit = cls.unit.to_string('latex')
                    except:
                        log.exception("Unit formatting failed for unit %s of trait %s, trying plain latex", cls.unit, cls)
                        raise
                        formatted_unit = ""

            log.info("Units formatting before modification for trait %s: %s", str(cls), formatted_unit)

            # For reasons that are not clear, astropy puts the \left and \right
            # commands outside of the math environment, so we must fix that
            # here.
            #
            # In fact, it appears that the units code is quite buggy.
            # @TODO: Review units code!
            if formatted_unit != "":
                formatted_unit = formatted_unit.replace("\r", "\\r")
                if not formatted_unit.startswith("$"):
                    formatted_unit = "$" + formatted_unit
                if not formatted_unit.endswith("$"):
                    formatted_unit = formatted_unit + "$"
                formatted_unit = re.sub(r"\$\\(left|right)(\S)\$", r"\\\1\2", formatted_unit)
                if not formatted_unit.startswith("$"):
                    formatted_unit = "$" + formatted_unit
                if not formatted_unit.endswith("$"):
                    formatted_unit = formatted_unit + "$"

                formatted_unit = formatted_unit.replace("{}^{\\prime\\prime}", "arcsec")

            # Return the final value, with the multiplier attached
            if hasattr(cls.unit, 'value'):
                formatted_unit = "{0.value:0.03g} {1}".format(cls.unit, formatted_unit)
            log.info("Units final formatting for trait %s: %s", str(cls), formatted_unit)
            return formatted_unit
        else:
            return ""


class Trait(BaseTrait):
    pass


class TraitCollection(BaseTrait):
    pass
