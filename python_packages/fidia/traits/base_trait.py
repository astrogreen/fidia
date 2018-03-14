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
# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Generator, Union
import fidia

# Standard Library Imports
from collections import OrderedDict
import operator

# Other library imports

# FIDIA Imports
# from fidia.exceptions import *
import fidia.base_classes as bases
from fidia.utilities import is_list_or_set, fidia_classname
# Other modules within this FIDIA sub-package
from .trait_utilities import TraitMapping, SubTraitMapping, TraitPointer, TraitProperty, SubTrait, TraitKey, \
    validate_trait_version, validate_trait_branch

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


__all__ = ['Trait', 'TraitCollection']

# def validate_trait_branches_versions_dict(branches_versions):
#     # type: ([BranchesVersions, None]) -> None
#     if branches_versions is None:
#         return
#     assert isinstance(branches_versions, dict), "`branches_versions` must be a dictionary"
#     # Check that all branches meet the branch formatting requirements
#     for branch in branches_versions:
#         if branch is not None:
#             validate_trait_branch(branch)
#         # Check that each branch has a list of versions:
#         assert is_list_or_set(branches_versions[branch])
#         # Check that all versions meet the branch formatting requirements
#         for version in branches_versions[branch]:
#             if version is not None:
#                 validate_trait_version(version)


class BaseTrait(bases.BaseTrait):
    """A class defining the common methods for both Trait and TraitCollection.

    Trait and TraitCollection have different meanings conceptually, but
    are very similar in functionality. This class provides all of the similar
    functionality between Trait and TraitCollection.

    """


    # The following are a required part of the Trait interface.
    # They must be set in sub-classes to avoid an error trying create a Trait.
    # trait_type = None


    # NOTE: Branches and versions are not currently implemented.
    # branches_versions = None


    # _trait_class_initialized = False

    #             ___               __                       __       ___    __
    #    | |\ | |  |      /\  |\ | |  \    \  /  /\  |    | |  \  /\   |  | /  \ |\ |
    #    | | \| |  |     /~~\ | \| |__/     \/  /~~\ |___ | |__/ /~~\  |  | \__/ | \|
    #

    @classmethod
    def _initialize_trait_class(cls):
        """Steps to initialize a Trait class.

        Steps are:

        1.  Make sure all of the TraitProperty descriptors (which define the
            slots of the Trait that must be populated by the mapping) have their
            names set to match the attribute that references them (this could be
            done by passing the name in the creation of the TraitProperty, but
            it feels very redundant, and would have to be checked anyway.

        2.  Do the same for SubTrait descriptors.

        Implementation Note
        -------------------

        Getting this working is more subtle than I thought. Basically, we have
        some code here that must be run once for each sub-class of `BaseTrait`.
        To check if the code has run, we want to store some flag when it's run
        the first time that shows that it has been run. Storing this flag is
        more difficult than I thought! Currently, what is done is attributes are
        added to the class, and then we check if these are present and have the
        right value, and if not, we assume that we need to initialize the
        class.

        In this way, if we encounter a subclass of a Trait class, we can
        identify if it has not been initialized even if the superclass has been.

        """

        # This try-except-else block checks if this class has been initialized.
        try:
            assert isinstance(cls._trait_properties_initialized, set) and cls._trait_init_name == fidia_classname(cls)
        except:
            pass
            # This class needs initialization, done below.
        else:
            log.debug("Trait class %s already initialised as %s", cls, cls._trait_init_name)
            if log.isEnabledFor(slogging.DEBUG):
                for attr in cls._trait_property_slots(_init_trait=False):
                    tp = getattr(cls, attr)  # type: TraitProperty
                    if tp.name is None:
                        log.debug("...but TraitProperty %s is not initialised", attr)
                        log.debug("%s", cls._trait_init_name)
                        log.debug("%s", cls._trait_properties_initialized)
                        if tp.name in cls._trait_properties_initialized:
                            log.debug("...and it previously was?!!")
            return

        log.debug("Initializing Trait Class %s", cls)

        cls._trait_properties_initialized = set()

        # Make sure all attached TraitProperties have their names set:
        for attr in cls._trait_property_slots(_init_trait=False):
            tp = getattr(cls, attr)  # type: TraitProperty
            if tp.name is None:
                tp.name = attr
            else:
                assert tp.name == attr, \
                    "Trait property has name %s, but is associated with attribute %s" % (tp.name, attr)
            cls._trait_properties_initialized.add(attr)

        # Make sure all attached SubTraits have their names set:
        for attr in cls._sub_trait_slots(_init_trait=False):
            st = getattr(cls, attr)  # type: Trait
            if st.name is None:
                st.name = attr
            else:
                assert st.name == attr, \
                    "Sub-trait has name %s, but is associated with attribute %s" % (tp.name, attr)
            cls._trait_properties_initialized.add(attr)

        # Initialization complete. Clean up.
        log.debug("Initialized Trait class %s", str(cls))

        cls._trait_init_name = fidia_classname(cls)


    def __init__(self, sample, trait_key, astro_object, trait_mapping):
        # type: (fidia.Sample, TraitKey, Union[fidia.AstronomicalObject, None], Union[TraitMapping, SubTraitMapping]) -> None

        # This function should only be called by:
        #
        #   - TraitPointers when they are asked to create a particular Trait
        #   - (unnamed) SubTrait objects when they are asked to return a sub-Trait of an existing Trait.

        log.debug("Initializing Trait: %s, %s", trait_key, trait_mapping)

        cls = type(self)

        #   This might be a good thing to put in place, as it helps to guarantee
        #   that these base classes remain pristine.
        # if cls is BaseTrait or cls is Trait or cls is TraitCollection:
        #     raise Exception("Cannot instanciate base Trait classes, only sub-classes.")

        super(BaseTrait, self).__init__()


        # self._validate_trait_class()

        self._sample = sample
        assert isinstance(self._sample, bases.Sample)
        # self._parent_trait = parent_trait

        # assert isinstance(trait_key, TraitKey), \
        #   "In creation of Trait, trait_key must be a TraitKey, got %s" % trait_key
        self._trait_key = trait_key

        # self._set_branch_and_version(trait_key)

        self._astro_object = astro_object
        # NOTE: The special value `None` is used for when this Trait refers to all
        # objects in the sample, rather than a single object.
        if self._astro_object is None:
            self.object_id = None
        else:
            assert isinstance(self._astro_object, fidia.AstronomicalObject)
            self.object_id = astro_object.identifier

        self._trait_mapping = trait_mapping
        assert isinstance(self._trait_mapping, (TraitMapping, SubTraitMapping))

        self._trait_cache = OrderedDict()

        cls = type(self)
        cls._initialize_trait_class()

    def _post_init(self):
        pass

    def __iter__(self):
        """Allow iteration over a Trait if it does not point to a single data object, but instead to the whole sample.

        Notes
        -----

        I'm not fully sure if this functionality is necessary or not, but I'm
        going to implement it for now since I know how to do it and it won't be
        much work.  -AGreen

        """
        if self.object_id is not None:
            raise TypeError("Trait object is not iterable when it references a single data-object.")
        else:
            for object_id in self._sample.contents:
                # Create a Trait identical to this one, but with a pointer to an individual data object.
                yield self.__class__(self._sample, self._trait_key, self._sample[object_id], self._trait_mapping)


    @classmethod
    def _validate_trait_class(cls):

        # NOTE: Branch and versions are not currently implemented so the code below is commented out.

        # assert cls.available_versions is not None
        #
        # if cls.branches_versions is not None:
        #     if not isinstance(cls.branches_versions, BranchesVersions):
        #         cls.branches_versions = BranchesVersions(cls.branches_versions)
        #     if getattr(cls, 'defaults', None) is None:
        #         # Defaults not provided. See if only one branch/version are supplied
        #         if cls.branches_versions.has_single_branch_and_version():
        #             # Set the defaults to be the only branch/version:
        #             cls.defaults = cls.branches_versions.as_defaults()  # type: DefaultsRegistry
        #             log.debug(cls.defaults._default_branch)
        #             log.debug(cls.defaults._version_defaults)
        #         else:
        #             raise Exception("Trait class '%s' has branches_versions, but no defaults have been supplied." %
        #                     cls)
        #
        # try:
        #     validate_trait_branches_versions_dict(cls.branches_versions)
        # except AssertionError as e:
        #     raise TraitValidationError(e.args[0] + " on trait class '%s'" % cls)

        pass


    @property
    def trait_name(self):
        return self._trait_key.trait_name


    @classmethod
    def trait_class_name(cls):
        return fidia_classname(cls)

    #  __       ___          __   ___ ___  __     ___
    # |  \  /\   |   /\     |__) |__   |  |__) | |__  \  /  /\  |
    # |__/ /~~\  |  /~~\    |  \ |___  |  |  \ | |___  \/  /~~\ |___
    #

    def _get_column_data(self, column_id):
        """For a requested column id, return the corresponding data.

        This finds the necessary column instance and it's corresponding archive,
        retrieves the necessary `archive_id` corresponding to self's `object_id`
        and then calls the `.get_value` method.

        This function does (should) handle ALL data access in FIDIA Traits.

        """
        archive = self._sample.archive_for_column(column_id)
        column = self._sample.find_column(column_id)
        if self.object_id is not None:
            # Operating on a single data object.
            archive_object_id = self._sample.get_archive_id(archive, self.object_id)
            value = column.get_value(archive_object_id)
            return value
        else:
            # Operating on all objects in the sample.
            if isinstance(column, fidia.FIDIAArrayColumn):
                # We have an array column: return an iterator that iterates over all values
                for object_id in self._sample.contents:
                    print(column.get_value(self._sample.get_archive_id(archive, object_id)))

                # NOTE: this line won't work because the generator can only be
                # used once. I'm leaving it here to remind me not to try it
                # again, as it seems much more elegant than the solution below.
                ### return (column.get_value(self._sample.get_archive_id(archive, object_id))
                ###        for object_id in self._sample.contents)

                class _ResultIterator:
                    def __init__(self, trait):
                        assert isinstance(trait, BaseTrait)
                        self.trait = trait

                    def gen(self, trait):
                        for object_id in trait._sample.contents:
                            archive_object_id = trait._sample.get_archive_id(archive, object_id)
                            yield column.get_value(archive_object_id)

                    def __iter__(self):
                        return iter(self.gen(self.trait))

                return _ResultIterator(self)

            else:
                # We have a non-array column: return an array of results
                result = column.get_array()
                return result

    #       ___ ___       __       ___
    # |\/| |__   |   /\  |  \  /\   |   /\
    # |  | |___  |  /~~\ |__/ /~~\  |  /~~\
    #
    # Functions to retrieve metadata on the mapped attributes, particularly TraitProperties.

    def _get_column_for_trait_property(self, attr):
        # type: (str) -> fidia.column.FIDIAColumn
        """Given the name of a TraitProperty, return the corresponding FIDIAColumn object."""
        column_id = self._trait_mapping.trait_property_mappings[attr].id
        column = self._sample.find_column(column_id)
        return column

    def get_pretty_name(self, attr):
        if attr in self.dir_trait_properties():
            # item is a TraitProperty
            column = self._get_column_for_trait_property(attr)
            return column.pretty_name

    def get_short_description(self, attr):
        if attr in self.dir_trait_properties():
            # item is a TraitProperty
            column = self._get_column_for_trait_property(attr)
            return column.short_description

    def get_long_description(self, attr):
        if attr in self.dir_trait_properties():
            # item is a TraitProperty
            column = self._get_column_for_trait_property(attr)
            return column.long_description

    def get_unit(self, attr):
        if attr in self.dir_trait_properties():
            # item is a TraitProperty
            column = self._get_column_for_trait_property(attr)
            return column.unit

    def get_ucd(self, attr):
        if attr in self.dir_trait_properties():
            # item is a TraitProperty
            column = self._get_column_for_trait_property(attr)
            return column.ucd


    # Relevant section of code from the function `.as_specification_dict`:
    #
    #     result = {self.name: OrderedDict([
    #         ("name", self.name),
    #         ("pretty_name", column.pretty_name),
    #         ("column_id", self.id),
    #         ("dtype", str(column.dtype)),
    #         ("n_dim", column.n_dim),
    #         ("unit", column.unit),
    #         ("ucd", column.ucd),
    #         ("short_description", column.short_description),
    #         ("long_description", column.long_description)
    #     ])}

    #            __   __   ___  __          ___ ___  __     __       ___  ___  __
    # |\/|  /\  |__) |__) |__  |  \     /\   |   |  |__) | |__) |  |  |  |__  /__`
    # |  | /~~\ |    |    |___ |__/    /~~\  |   |  |  \ | |__) \__/  |  |___ .__/
    #
    # Directories of mapped attributes on this Trait, and related helper methods.
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
        if hasattr(self, '_trait_mapping'):
            return list(self._trait_mapping.trait_property_mappings.keys())
        else:
            return []

    def dir_sub_traits(self):
        # type: () -> List[str]
        """Return a directory of the SubTraits for this Trait, similar to what the builtin `dir()` does.

        This result is based on the actual mapping for this Trait (instance).

        """
        if hasattr(self, '_trait_mapping') and hasattr(self._trait_mapping, 'sub_trait_mappings'):
            return list(self._trait_mapping.sub_trait_mappings.keys())
        else:
            return []

    def dir_named_sub_traits(self):
        # type: () -> List[str]
        """Return a directory of the Named SubTraits for this Trait, similar to what the builtin `dir()` does.

        This result is based on the actual mapping for this Trait (instance).

        """
        if hasattr(self, '_trait_mapping') and hasattr(self._trait_mapping, 'named_sub_mappings'):
            return list(set(map(operator.itemgetter(0), self._trait_mapping.named_sub_mappings.keys())))
        else:
            return []

    def __dir__(self):
        # noinspection PyUnresolvedReferences
        parent_dir = list(super(BaseTrait, self).__dir__())
        return parent_dir + self.dir_named_sub_traits() + self.dir_sub_traits() + self.dir_trait_properties()

    @classmethod
    def _trait_property_slots(cls, return_object=False, trait_property_types=None, _init_trait=True):
        # type: (bool, List, bool) -> Generator[Union[TraitProperty, str]]
        """List of TraitProperty "slots" defined on this Trait class, similar to builtin `dir`.

        This is different from `.dir_trait_properties`: This function reflects
        the Trait class definition, while the other one reflects the actual
        mapping defined for this trait. Hence this is a class method, while the
        other function is (necessarily) an instance method.

        :param trait_property_types:
            Either a string trait type or a list of string trait types or None.
            None will return all trait types, otherwise only traits of the
            requested type are returned.

        :param return_object:
            If True, return the TraitProperty object instead of the string name of
            the attribute.

        :returns:
            A TraitProperty object, which is a descriptor that can retrieve data.

        Note that the TraitProperty descriptor must be handed this Trait object
        to actually retrieve data.

        This basically extends the private method _trait_property_slots to
        return the actual descriptor object.

        """

        if _init_trait:
            cls._initialize_trait_class()

        if isinstance(trait_property_types, str):
            trait_property_types = (trait_property_types,)

        # Search class attributes:
        log.debug("Searching for TraitProperties of Trait '%s' with type in %s", cls.__name__, trait_property_types)
        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, TraitProperty):
                # if obj.name.startswith("_") and not include_hidden:
                #     log.debug("Trait property '%s' ignored because it is hidden.", attr)
                #     continue
                # log.debug("Found trait property '{}' of type '{}'".format(attr, obj.dtype))
                log.debug("Found trait property {tp!r}".format(tp=obj))
                if (trait_property_types is None) or (obj.type in trait_property_types):
                    yield (obj if return_object else attr)

    @classmethod
    def _sub_trait_slots(cls, return_object=False, _init_trait=True):
        # type: (bool, bool) -> Generator[Union[SubTrait, str]]
        """List of SubTrait "slots" defined on this Trait class, similar to builtin `dir`.

        This is different from `.dir_sub_traits`: This function reflects
        the Trait class definition, while the other one reflects the actual
        mapping defined for this trait. Hence this is a class method, while the
        other function is (necessarily) an instance method.

        :param return_object:
            If True, return the TraitProperty object instead of the string name of
            the attribute.

        """

        if _init_trait:
            cls._initialize_trait_class()

        for attr in dir(cls):
            obj = getattr(cls, attr)
            if isinstance(obj, SubTrait):
                yield (obj if return_object else attr)


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

    def __repr__(self):
        return "<Trait class '{classname}': {trait_type}>".format(
            classname=fidia_classname(self),
            trait_type=self.__class__.__name__)

    def _repr_pretty_(self, p, cycle):
        # p.text(self.__str__())
        if cycle:
            p.text(self.__str__())
        else:
            p.text("FIDIA {} Trait \"{}\"".format(fidia_classname(self), str(self._trait_key)))
            if self.object_id is None:
                p.text(" on all objects in {}".format(self._sample))
            else:
                p.text(" on object {}".format(self.object_id))
            with p.group(4):
                p.break_()
                sub_traits = self.dir_sub_traits()
                if sub_traits:
                    with p.group(4, "Sub-traits:"):
                        p.breakable()
                        for name in sub_traits:
                            p.text(name)
                            p.breakable()
                named_sub_traits = self.dir_named_sub_traits()
                if named_sub_traits:
                    with p.group(4, "Named sub-traits:"):
                        p.breakable()
                        for name in named_sub_traits:
                            p.text(name)
                            p.breakable()
                properties = self.dir_trait_properties()
                if properties:
                    with p.group(4, "Trait Properties:"):
                        p.breakable()
                        for name in properties:
                            p.text(name)
                            p.breakable()


    def __str__(self):
        formatted_named_sub_traits = ", ".join(self.dir_named_sub_traits())
        formatted_sub_traits = ", ".join(self.dir_sub_traits())
        formatted_trait_properties = ", ".join(self.dir_trait_properties())

        return """{trait_repr}
        Sub-traits:
            [{st}]
        Trait Properities:
            [{tp}]
        Named sub-traits:
            [{nst}]
        """.format(
            trait_repr=repr(self),
            st=formatted_sub_traits, tp=formatted_trait_properties, nst=formatted_named_sub_traits)

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

        if item.startswith("_"):
            # This won't handle any private items, so raise an attribute error
            # immediately to avoid potential infinite recursion.
            raise AttributeError("Unknown attribute %s for TraitCollection object." % item)

        if item in map(operator.itemgetter(0), self._trait_mapping.named_sub_mappings.keys()):
            # item is a Trait or TraitCollection, so should return a
            # TraitPointer object with the corresponding sub-schema.
            return TraitPointer(item, self._sample, self._astro_object, self._trait_mapping.named_sub_mappings)

        elif item in self._trait_mapping.trait_property_mappings:
            # item is a TraitProperty. Behave like TraitProperty
            column_id = self._trait_mapping.trait_property_mappings[item].id
            # Get the result
            result = self._get_column_data(column_id)
            # Cache the result against the trait (so this code will not be called again!)
            setattr(self, item, result)
            return result

        else:
            if "_trait_mapping" in self.__dict__:
                log.warn("Unknown attribute %s for object %s", item, self)
                log.warn("  Known Trait Mappings: %s", list(self._trait_mapping.named_sub_mappings.keys()))
                log.warn("  Known Trait Properties: %s", list(self._trait_mapping.trait_property_mappings.keys()))

            raise AttributeError("Unknown attribute %s for TraitCollection object." % item)

    # def __str__(self):
    #     return """TraitCollection: {schema}""".format(schema=self._trait_mapping)
