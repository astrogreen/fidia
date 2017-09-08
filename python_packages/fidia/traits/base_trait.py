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

from typing import List, Generator, Union
import fidia

# Standard Library Imports
from collections import OrderedDict
import operator

# Other library imports

# FIDIA Imports
from fidia.exceptions import *
import fidia.base_classes as bases
from fidia.utilities import is_list_or_set, DefaultsRegistry, fidia_classname
# Other modules within this FIDIA sub-package
from .trait_utilities import TraitMapping, SubTraitMapping, TraitPointer, TraitProperty, SubTrait, TraitKey, \
    validate_trait_version, validate_trait_branch, \
    BranchesVersions

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


__all__ = ['Trait', 'TraitCollection']

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


class BaseTrait(bases.BaseTrait):
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

    # extensible = False

    descriptions_allowed = 'class'

    _trait_class_initialized = False

    #             ___               __                       __       ___    __
    #    | |\ | |  |      /\  |\ | |  \    \  /  /\  |    | |  \  /\   |  | /  \ |\ |
    #    | | \| |  |     /~~\ | \| |__/     \/  /~~\ |___ | |__/ /~~\  |  | \__/ | \|
    #

    @classmethod
    def _initialize_trait_class(cls):
        """Steps to initialize a Trait class."""

        if not cls._trait_class_initialized:
            # Make sure all attached TraitProperties have their names set:
            for attr in cls._trait_property_slots():
                tp = getattr(cls, attr)  # type: TraitProperty
                if tp.name is None:
                    tp.name = attr
                else:
                    assert tp.name == attr, \
                        "Trait property has name %s, but is associated with attribute %s" % (tp.name, attr)
            # Make sure all attached SubTraits have their names set:
            for attr in cls._sub_trait_slots():
                tp = getattr(cls, attr)  # type: Trait
                if tp.name is None:
                    tp.name = attr
                else:
                    assert tp.name == attr, \
                        "Trait property has name %s, but is associated with attribute %s" % (tp.name, attr)

            # Initialization complete. Clean up.
            log.debug("Initialized Trait class %s", str(cls))
            cls._trait_class_initialized = True

    def __init__(self, sample, trait_key, astro_object, trait_mapping):
        # type: (fidia.Sample, TraitKey, fidia.AstronomicalObject, Union[TraitMapping, SubTraitMapping]) -> None

        # This function should only be called by:
        #
        #   - TraitPointers when they are asked to create a particular Trait
        #   - (unnamed) SubTrait objects when they are asked to return a sub-Trait of an existing Trait.

        super(BaseTrait, self).__init__()


        # self._validate_trait_class()

        self.sample = sample
        assert isinstance(self.sample, bases.Sample)
        # self._parent_trait = parent_trait

        # assert isinstance(trait_key, TraitKey), \
        #   "In creation of Trait, trait_key must be a TraitKey, got %s" % trait_key
        self.trait_key = trait_key

        # self._set_branch_and_version(trait_key)

        self.astro_object = astro_object
        assert isinstance(self.astro_object, fidia.AstronomicalObject)
        self.object_id = astro_object.identifier

        self.trait_mapping = trait_mapping
        assert isinstance(self.trait_mapping, (TraitMapping, SubTraitMapping))

        self._trait_cache = OrderedDict()

        if not self._trait_class_initialized:
            cls = type(self)
            cls._initialize_trait_class()


    def _get_column_data(self, column_id):
        """For a requested column id, return the corresponding data.

        This finds the necessary column instance and it's corresponding archive,
        retrieves the necessary `archive_id` corresponding to self's `object_id`
        and then calls the `.get_value` method.

        """
        archive = self.sample.archive_for_column(column_id)
        column = self.sample.find_column(column_id)
        archive_id = self.sample.get_archive_id(archive, self.object_id)
        value = column.get_value(archive_id)
        return value

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


    @classmethod
    def trait_class_name(cls):
        return fidia_classname(cls)


    #
    # ___  __         ___  __   __   __   __   ___  __  ___                        __               __
    #  |  |__)  /\  |  |  |__) |__) /  \ |__) |__  |__)  |  \ /    |__|  /\  |\ | |  \ |    | |\ | / _`
    #  |  |  \ /~~\ |  |  |    |  \ \__/ |    |___ |  \  |   |     |  | /~~\ | \| |__/ |___ | | \| \__>

    @classmethod
    def trait_properties(cls, trait_property_types=None, include_hidden=False):
        # type: (List, bool) -> Generator[TraitProperty]
        """Generator which iterates over the TraitProperties attached to this Trait.

        :param trait_property_types:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        :returns: 
            A TraitProperty object, which is a descriptor that can retrieve data.

        Note that the TraitProperty descriptor must be handed this Trait object
        to actually retrieve data.

        """
        cls._initialize_trait_class()


        if isinstance(trait_property_types, str):
            trait_property_types = (trait_property_types, )

        # Search class attributes:
        log.debug("Searching for TraitProperties of Trait '%s' with type in %s", cls.trait_type, trait_property_types)
        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, TraitProperty):
                # if obj.name.startswith("_") and not include_hidden:
                #     log.debug("Trait property '%s' ignored because it is hidden.", attr)
                #     continue
                log.debug("Found trait property '{}' of type '{}'".format(attr, obj.type))
                if (trait_property_types is None) or (obj.type in trait_property_types):
                    yield obj


    # Directories of mapped attributes on this Trait.
    #
    # Traits and TraitCollections can have trait properties, (unnamed)
    # sub-traits, and named sub-traits. Since which of these are present
    # is often only known by looking at the mapping, we do exactly that
    # here to provide lists of the known attributes of this object. These
    # attributes may not necessarily be present---instead, they may be
    # provided dynamically by `__getattr__`.

    # @TODO: There are no tests of these functions!

    def dir_trait_properties(self):
        # type: () -> List[str]
        """Return a directory of TraitProperties for this object, similar to what the builtin `dir()` does.

        This result is based on the actual mapping for this Trait (instance).

        """
        return list(self.trait_mapping.trait_property_mappings.keys())

    def dir_sub_traits(self):
        # type: () -> List[str]
        """Return a directory of the SubTraits for this Trait, similar to what the builtin `dir()` does.

        This result is based on the actual mapping for this Trait (instance).

        """
        if hasattr(self.trait_mapping, 'sub_trait_mappings'):
            return list(self.trait_mapping.sub_trait_mappings.keys())
        else:
            return []

    def dir_named_sub_traits(self):
        # type: () -> List[str]
        """Return a directory of the Named SubTraits for this Trait, similar to what the builtin `dir()` does.

        This result is based on the actual mapping for this Trait (instance).

        """
        if hasattr(self.trait_mapping, 'named_sub_mappings'):
            return list(set(map(operator.itemgetter(0), self.trait_mapping.named_sub_mappings.keys())))
        else:
            return []

    def __dir__(self):
        # noinspection PyUnresolvedReferences
        parent_dir = super(BaseTrait, self).__dir__()
        return parent_dir + self.dir_named_sub_traits() + self.dir_sub_traits() + self.dir_trait_properties()

    @classmethod
    def _trait_property_slots(cls):
        """List of TraitProperty "slots" defined on this Trait class, similar to builtin `dir`.

        This is different from `.dir_trait_properties`: This function reflects
        the Trait class definition, while the other one reflects the actual
        mapping defined for this trait. Hence this is a class method, while the
        other function is (necessarily) an instance method.

        """
        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, TraitProperty):
                yield attr

    @classmethod
    def _sub_trait_slots(cls):
        """List of SubTrait "slots" defined on this Trait class, similar to builtin `dir`.

        This is different from `.dir_sub_traits`: This function reflects
        the Trait class definition, while the other one reflects the actual
        mapping defined for this trait. Hence this is a class method, while the
        other function is (necessarily) an instance method.

        """

        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, SubTrait):
                yield attr


    #  __       ___          ___      __   __   __  ___           ___ ___       __   __   __
    # |  \  /\   |   /\     |__  \_/ |__) /  \ |__)  |      |\/| |__   |  |__| /  \ |  \ /__`
    # |__/ /~~\  |  /~~\    |___ / \ |    \__/ |  \  |      |  | |___  |  |  | \__/ |__/ .__/
    #
    # Note: Only data export methods which make sense for *any* trait are
    # defined here. Other export methods, such as FITS Export, are defined in
    # mixin classes.

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
        return "<Trait class '{classname}': {trait_type}>".format(
            classname=fidia_classname(self),
            trait_type=self.trait_type)



class Trait(bases.Trait, BaseTrait):
    pass


class TraitCollection(bases.TraitCollection, BaseTrait):

    def __getattr__(self, item):
        log.debug("Looking up %s on TraitCollection %s", item, self)

        # There are basically two cases we must handle here. We can determine
        # between these two cases by looking at the type of the object in the
        # trait schema, and responding as follows:
        #
        #   1. (TraitMapping) The item requested is a Trait or TraitCollection, in which case
        #   we need to create and return a TraitPointer object
        #
        #   2. (str) The item requested is a TraitProperty, in which case we need to
        #   look up the column and return the result as though we had called an
        #   actual TraitProperty object.


        if item in map(operator.itemgetter(0), self.trait_mapping.named_sub_mappings.keys()):
            # item is a Trait or TraitCollection, so should return a
            # TraitPointer object with the corresponding sub-schema.
            return TraitPointer(item, self.sample, self.astro_object, self.trait_mapping)

        elif item in self.trait_mapping.trait_property_mappings:
            # item is a TraitProperty. Behave like TraitProperty
            column_id = self.trait_mapping.trait_property_mappings[item].id
            # Get the result
            result = self._get_column_data(column_id)
            # Cache the result against the trait (so this code will not be called again!)
            setattr(self, item, result)
            return result

        else:
            log.warn("Unknown attribute %s for object %s", item, self)
            log.warn("  Known Trait Mappings: %s", list(self.trait_mapping.named_sub_mappings.keys()))
            log.warn("  Known Trait Properties: %s", list(self.trait_mapping.trait_property_mappings.keys()))

            raise AttributeError("Unknown attribute %s for object %s" % (item, self))

    def __str__(self):
        return """TraitCollection: {schema}""".format(schema=self.trait_mapping)