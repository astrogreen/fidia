"""
Traits are the composite data types in FIDIA. They collect together columns of atomic data
into larger, more useful structures.

Traits are hierarchical
-----------------------

`.Traits` and `.TraitCollections` can contain other `.Traits` or `.TraitCollections` as well as
atomic data.


Defining Traits
---------------

A trait of a particular type defines the data that must be associated with it. For example, an
Image trait might require not only the 2D array of image values, but also information on where
in the sky it was taken, and what filters were used.

A subclass of a `.Trait` defines the required data by including `.TraitProperties` for each
column of atomic data required. `.TraitProperties` can include information about what type
that data must have, e.g. int, float, string, array dimensions, etc.


Trait instance creation
-----------------------

`.Trait` instances are created by `.TraitPointer` instances when requested by the user.
`.TraitPointers` validate the user provided `.TraitKey` against the schema stored in the
`.TraitRegistry` and then initialize the `.Trait` with instructions on how to link the
`.TraitProperties` to actual columns of data.

The linking instructions take the form of a Python `dict` of column references
keyed by the `.TraitProperty`'s name. These instructions are executed by
`.Trait._link_columns()`.


"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Generator
import fidia.base_classes as bases

# Standard Library Imports
import pickle
from io import BytesIO
from collections import OrderedDict, Mapping
from copy import copy
import re


# Other library imports
from astropy.io import fits

# FIDIA Imports
from fidia.exceptions import *
import fidia.base_classes as bases
from fidia.utilities import SchemaDictionary, is_list_or_set, DefaultsRegistry, RegexpGroup, snake_case
from fidia.descriptions import TraitDescriptionsMixin, DescriptionsMixin
# Other modules within this FIDIA sub-package
from .trait_property import TraitProperty
from .trait_key import TraitKey, TraitPath, TRAIT_NAME_RE, \
    validate_trait_name, validate_trait_version, validate_trait_branch, \
    BranchesVersions
from .trait_registry import TraitRegistry

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


class ColumnProxy:
    def __init__(self, column_id):
        self.column_id = column_id

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._get_column_data(self.column_id)

class BaseTrait(TraitDescriptionsMixin, bases.BaseTrait):
    """A class defining the common methods for both Trait and TraitCollection.

    Trait and TraitCollection have different meanings conceptually, but
    are very similar in functionality. This class provides all of the similar
    functionality between Trait and TraitCollection.

    """


    # The following are a required part of the Trait interface.
    # They must be set in sub-classes to avoid an error trying create a Trait.
    trait_type = None
    qualifiers = None
    branches_versions = None

    extensible = False

    descriptions_allowed = 'class'

    #             ___               __                       __       ___    __
    #    | |\ | |  |      /\  |\ | |  \    \  /  /\  |    | |  \  /\   |  | /  \ |\ |
    #    | | \| |  |     /~~\ | \| |__/     \/  /~~\ |___ | |__/ /~~\  |  | \__/ | \|
    #

    def __init__(self, sample, trait_key, object_id, trait_registry, trait_schema):
        # type: (bases.Sample, bases.TraitKey, str, bases.TraitRegistry, dict) -> None
        super(BaseTrait, self).__init__()


        self._validate_trait_class()

        self.sample = sample
        # self._parent_trait = parent_trait

        # assert isinstance(trait_key, TraitKey), "In creation of Trait, trait_key must be a TraitKey, got %s" % trait_key
        self.trait_key = trait_key

        # self._set_branch_and_version(trait_key)

        self.object_id = object_id

        self.trait_schema = trait_schema
        self._link_columns()

        self._trait_cache = OrderedDict()


        for key in trait_schema:
            setattr(self, key, ColumnProxy(column_id=trait_schema[key]))

        # if parent_trait is not None:
        #     self.trait_path = TraitPath(parent_trait.trait_path + (self.trait_key, ))
        # else:
        #     self.trait_path = TraitPath([self.trait_key])

    def _get_column_data(self, column_id):
        archive = self.sample.archive_for_column(column_id)
        column = self.sample.find_column(column_id)
        archive_id = self.sample.get_archive_id()
        column.get_value(archive_id)

    def _post_init(self):
        pass

    @classmethod
    def _validate_trait_class(cls):
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



    @property
    def trait_name(self):
        return self.trait_key.trait_name




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
        # type: (List, bool) -> Generator[TraitProperty]
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

    def _link_columns(self):
        """Create links to actual columns based on the column references associated with this trait."""

        # A local copy of the schema we chan change
        schema = copy(self.trait_schema)

        # @TODO: Handle sub-traits in the schema

        # Iterate over trait properties, populating them as needed from the trait_schema.
        for tp in self._trait_properties():
            if tp.required and tp.name not in schema:
                raise FIDIAException
            reference = schema.pop(tp.name)

            # @TODO: Convert reference into column link

            setattr(self, tp.name, reference)

        # Set any extra columns defined for this trait (not in the required list)
        if self.extensible:
            for reference_name in schema:
                reference = schema[reference_name]
                if isinstance(reference, ColumnReference):
                    # @TODO: Define column reference
                    setattr(self, reference_name, schema[reference_name])

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

    def __str__(self):
        return "<Trait class '{classname}': {trait_type}>".format(classname=self.__class__.__name__, trait_type=self.trait_type)



class Trait(bases.Trait, BaseTrait):
    pass


class TraitCollection(bases.TraitCollection, BaseTrait):
    pass
