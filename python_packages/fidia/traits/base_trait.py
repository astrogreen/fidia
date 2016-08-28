
# Standard Library Imports
import pickle
from io import BytesIO
from collections import OrderedDict, Mapping

from contextlib import contextmanager

# Other library imports
from astropy.io import fits

# Internal package imports
from .abstract_base_traits import *
from ..exceptions import *
from .trait_property import TraitProperty
from .trait_key import TraitKey, TRAIT_NAME_RE, \
    validate_trait_type, validate_trait_qualifier, validate_trait_version, validate_trait_branch
from .trait_registry import TraitRegistry
from ..utilities import SchemaDictionary, is_list_or_set, Inherit
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
    # type: ([dict, None]) -> None
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

class Trait(TraitDescriptionsMixin, AbstractBaseTrait):

    # The following are a required part of the Trait interface.
    # They must be set in sub-classes to avoid an error trying create a Trait.
    trait_type = None
    qualifiers = None
    branches_versions = None

    descriptions_allowed = 'class'

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


        assert data_class in ('all', 'catalog', 'non-catalog', None)
        if data_class is None:
            data_class = 'all'

        schema = SchemaDictionary()
        for trait_property in cls._trait_properties():
            if data_class == 'all' or \
                    (data_class == 'catalog' and trait_property.type in TraitProperty.catalog_types) or \
                    (data_class == 'non-catalog' and trait_property.type in TraitProperty.non_catalog_types):
                schema[trait_property.name] = trait_property.type

        if include_subtraits:

            if by_trait_name:
                for trait_name in cls.sub_traits.get_trait_names():
                    # Create empty this sub-trait type:
                    schema[trait_name] = SchemaDictionary()

                    # Populate the dict with schema from each sub-type:
                    for trait_class in cls.sub_traits.get_trait_classes(trait_name_filter=trait_name):
                        # Recurse with the same options.
                        subtrait_schema = trait_class.schema(include_subtraits=include_subtraits,
                                                             by_trait_name=by_trait_name, data_class=data_class)
                        try:
                            schema[trait_name].update(subtrait_schema)
                        except ValueError:
                            log.error("Schema mis-match in traits: sub-trait '%s' cannot be added " +
                                      "to schema for '%s' containing: '%s'",
                                      trait_class, trait_name, schema[trait_name])
                            raise SchemaError("Schema mis-match in traits: sub-trait '%s' cannot be added " +
                                              "to schema for '%s' containing: '%s'",
                                              trait_class, trait_name, schema[trait_name])

            else:  # not by_trait_name
                log.debug("Building a schema for subtraits of '%s'", cls)
                trait_types = cls.sub_traits.get_trait_types()
                for trait_type in trait_types:
                    log.debug("    Processing traits with trait_name '%s'", trait_type)
                    schema[trait_type] = SchemaDictionary()
                    trait_names = cls.sub_traits.get_trait_names(trait_type_filter=trait_type)
                    for trait_name in trait_names:
                        trait_qualifier = TraitKey.split_trait_name(trait_name)[1]
                        if trait_name not in schema[trait_type]:
                            schema[trait_type][trait_qualifier] = SchemaDictionary()

                        # Populate the dict with schema from each sub-type:
                        for trait_class in cls.sub_traits.get_trait_classes(trait_name_filter=trait_name):
                            log.debug("        Attempting to add Trait class '%s'", trait_class)
                            # Recurse with the same options.
                            sub_trait_schema = trait_class.schema(include_subtraits=include_subtraits,
                                                                  by_trait_name=by_trait_name, data_class=data_class)
                            try:
                                schema[trait_type][trait_qualifier].update(sub_trait_schema)
                            except ValueError:
                                log.exception("Schema mis-match in traits: trait '%s' cannot be added " +
                                          "to schema for '%s' containing: '%s'",
                                          trait_class, trait_type, schema[trait_type][trait_name])
                                raise SchemaError("Schema mis-match in traits")

        if data_class != 'all':
            # Check for empty Trait schemas and remove:
            schema.delete_empty()

        return schema

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
            assert getattr(cls, 'defaults', None) is not None, \
                ("Trait class '%s' has branches_versions, but no defaults have been supplied." %
                 cls)

        try:
            validate_trait_branches_versions_dict(cls.branches_versions)
        except AssertionError as e:
            raise TraitValidationError(e.args[0] + " on trait class '%s'" % cls)

    def __init__(self, archive, trait_key=None, object_id=None, parent_trait=None, loading='lazy'):
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
            self.trait_path = parent_trait.trait_path + tuple(self.trait_key)
        else:
            self.trait_path = tuple(self.trait_key)


        # The preload count is used to track how many accesses there are to this
        # trait so that it can be properly cleaned up when all loads are
        # complete.
        self._preload_count = 0

        if loading not in ('eager', 'lazy', 'verylazy'):
            raise ValueError("loading keyword must be one of ('eager', 'lazy', 'verylazy')")
        self._loading = loading

        # Call user provided `init` funciton
        self.init()

        # Preload all traits
        # @TODO: Modify preloading to respect preload argument
        self._trait_dict = dict()
        if self._loading == 'eager':
            self._realise()
        self._post_init()

    def _post_init(self):
        pass

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

            if current_value not in (None, Inherit):
                # We have been given a (branch/version) value, check that it
                # is valid for this Trait:
                if valid is not None:
                    assert current_value in valid, \
                        "%s '%s' not valid for trait '%s'" % (attribute, current_value, self)
                return current_value
            elif current_value is Inherit:
                # We have been asked to inherit the branch/version from the
                # parent trait. If the parent_trait is defined (i.e. this is
                # not a top level trait), then take its value if it is valid
                # for this trait.
                if parent_trait is not None:
                    parent_value = getattr(parent_trait, attribute)
                    # This is a sub trait. Inherit branch from parent unless not valid.
                    if valid is not None and parent_value in valid:
                        return parent_value
                    else:
                        # Parent is not valid here, so leave as None
                        return None
            elif current_value is None:
                # Currently no way to define the branch/version for this
                # trait, so leave it as None.
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
    #  __             __             __        ___  __   __     __   ___  __
    # |__) |    |  | / _` | |\ |    /  \ \  / |__  |__) |__) | |  \ |__  /__`
    # |    |___ \__/ \__> | | \|    \__/  \/  |___ |  \ |  \ | |__/ |___ .__/
    #
    # The following three functions are for the "plugin-writter" to override.
    #

    def init(self):
        """Extra initialisations for a Trait.

        Override this function with any extra initialisation required for this
        trait, but not things such as opening files or connecting to a database:
        see `preload` and `cleanup` for those things.

        """
        pass

    def preload(self):
        """Prepare for a trait property to be retrieved using plugin code.

        Override this function with any initialisation required for this trait
        to load its data, such as opening required files, connecting to databases, etc.

        """
        pass

    def cleanup(self):
        """Cleanup after a trait property has been retrieved using plugin code.

        Override this function with any cleanup that should be done once this trait
        to loaded its data, such as closing files.

        """
        pass

    #
    # ___  __         ___  __   __   __   __   ___  __  ___                        __               __
    #  |  |__)  /\  |  |  |__) |__) /  \ |__) |__  |__)  |  \ /    |__|  /\  |\ | |  \ |    | |\ | / _`
    #  |  |  \ /~~\ |  |  |    |  \ \__/ |    |___ |  \  |   |     |  | /~~\ | \| |__/ |___ | | \| \__>

    @classmethod
    def _trait_properties(cls, trait_property_types=None):
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
                log.debug("Found trait property '{}' of type '{}'".format(attr, obj.type))
                if (trait_property_types is None) or (obj.type in trait_property_types):
                    yield obj

    @classmethod
    def trait_property_dir(cls):
        """Return a directory of TraitProperties for this object, similar to what the builtin `dir()` does."""
        for tp in cls._trait_properties():
            yield tp.name

    def trait_properties(self, trait_property_types=None):
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
                log.debug("Found trait property '{}' of type '{}'".format(attr, descriptor_obj.type))
                if (trait_property_types is None) or (descriptor_obj.type in trait_property_types):
                    # Retrieve the attribute for this object (which will create
                    # the BoundTraitProperty: see `__get__` on `TraitProperty`)
                    yield getattr(self, attr)

    def trait_property_values(self, trait_type=None):
        """Generator which returns the values of the TraitProperties of the given type.


        :return: the value of each TraitProperty (not the descriptor object)

        """
        for tp in self._trait_properties(trait_type):
            yield getattr(self, tp.name).value

    #
    #  __   __   ___       __        __          __
    # |__) |__) |__  |    /  \  /\  |  \ | |\ | / _`
    # |    |  \ |___ |___ \__/ /~~\ |__/ | | \| \__>
    #
    # Methods to handle loading the data associated with this Trait into memory.

    @contextmanager
    def preloaded_context(self):
        """Returns a context manager reference to the preloaded trait, and cleans up afterwards."""
        try:
            # Preload the Trait if necessary.
            self._load_incr()
            log.debug("Context manager version of Trait %s created", self.trait_key)
            yield self
        finally:
            # Cleanup the Trait if necessary.
            self._load_decr()
            log.debug("Context manager version of Trait %s cleaned up", self.trait_key)

    def _load_incr(self):
        """Internal function to handle preloading. Prevents a Trait being loaded multiple times.

        This function should be called prior to anything which requires calling
        TraitProperty loaders, typically only by the TraitProperty object
        itself.

        See also the `preloaded_context` function.
        """
        log.vdebug("Incrementing preload for trait %s", self.trait_key)
        assert self._preload_count >= 0
        try:
            if self._preload_count == 0:
                self.preload()
        except:
            log.exception("Exception in preloading trait %s", self.trait_key)
            raise
        else:
            self._preload_count += 1

    def _load_decr(self):
        """Internal function to handle cleanup.

        This function should be called after anything which requires calling
        TraitProperty loaders, typically only by the TraitProperty object
        itself.
        """
        log.vdebug("Decrementing preload for trait %s", self.trait_key)
        assert self._preload_count > 0
        try:
            if self._preload_count == 1:
                self.cleanup()
        except:
            raise
        else:
            self._preload_count -= 1

    def _realise(self):
        """Search through the objects members for TraitProperties, and preload any found.


        """

        log.debug("Realising...")

        # Check and if necessary preload the trait.
        self._load_incr()

        # Iterate over the trait properties, loading any not already in the
        # `_trait_dict` cache
        for traitprop in self._trait_properties():
            if traitprop.name not in self._trait_dict:
                self._trait_dict[traitprop.name] = traitprop.fload(self)

        # Check and if necessary cleanup the trait.
        self._load_decr()

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


    def __getitem__(self, key):
        # type: (TraitKey) -> Trait
        """Provide dictionary-like retrieve of sub-traits"""
        return self.get_sub_trait(key)


# class FITSExportMixin:
#     """A Trait Mixin class which adds FITS Export to the export options for a Trait."""

    def as_fits(self, file):
        """FITS Exporter

        :param  file
            file is either a file-like object, or a string containing the path
            of a file to be created. In the case of the string, the file will be
            created, written to, and closed.

        :returns None

        """

        assert isinstance(self, Trait)
        if not hasattr(self, 'value'):
            raise ExportException("Trait '%s' cannot be exported as FITS" % str(self))

        # Create a function holder which can be set to close the file if it is opened here
        file_cleanup = lambda: None
        if isinstance(file, str):
            file = open(file, 'wb')
            # Store pointer to close function to be called at the end of the this function.
            file_cleanup = file.close

        hdulist = fits.HDUList()

        # Check if a WCS is present as a SmartTrait:
        try:
            wcs_smarttrait = self['wcs']
        except KeyError:
            def add_wcs(hdu):
                return hdu
        else:
            def add_wcs(hdu):
                # type: (fits.PrimaryHDU) -> fits.PrimaryHDU
                hdu.header.extend(wcs_smarttrait.to_header())
                return hdu

        # Value should/will always be the first item in the FITS File (unless it cannot
        # be put in a PrimaryHDU, e.g. because it is not "image-like")

        if type(self).value.type in ("float.array", "int.array"):
            primary_hdu = fits.PrimaryHDU(self.value())
        elif type(self).value.type in ("float", "int"):
            primary_hdu = fits.PrimaryHDU([self.value()])
        else:
            log.error("Attempted to export trait with value type '%s'", type(self).value.type)
            file_cleanup()
            # @TODO: Delete the file (as it is invalid anyway)?
            raise ExportException("Trait '%s' cannot be exported as FITS" % str(self))

        # Add the newly created PrimaryHDU to the FITS file.
        add_wcs(primary_hdu)
        hdulist.append(primary_hdu)

        # Attach all "meta-data" Traits to Header of Primary HDU
        from . import meta_data_traits
        for sub_trait in self.get_all_subtraits():
            log.debug("Searching for metadata in subtrait '%s'...", sub_trait)
            if not isinstance(sub_trait, meta_data_traits.MetadataTrait):
                continue
            log.debug("Adding metadata trait '%s'", sub_trait)
            # MetadataTrait will have a bunch of Trait Properties which should
            # be appended individually, so we iterate over each Trait's
            # TraitProperties
            for trait_property in sub_trait.trait_properties(['float', 'int', 'string']):
                keyword_name = trait_property.get_short_name()
                keyword_value = trait_property.value
                keyword_comment = trait_property.get_description()
                log.debug("Adding metadata TraitProperty '%s' to header", keyword_name)
                primary_hdu.header[keyword_name] = (
                    keyword_value,
                    keyword_comment)

        # Attach all simple value Traits to header of Primary HDU:
        # for trait in self.get_sub_trait(Measurement):
        #     primary_hdu.header[trait.short_name] = (trait.value, trait.short_comment)
        #     primary_hdu.header[trait.short_name + "_ERR"] = (trait.value, trait.short_comment)

        # Create extensions for additional array-like values
        for trait_property in self.trait_properties(['float.array', 'int.array']):
            extension = fits.ImageHDU(trait_property.value)
            extension.name = trait_property.get_short_name()
            # Add the same WCS if appropriate
            add_wcs(extension)
            hdulist.append(extension)

        # Add single-numeric-value TraitProperties to the primary header:
        for trait_property in self.trait_properties(['float', 'int']):
            keyword_name = trait_property.get_short_name()
            keyword_value = trait_property.value
            keyword_comment = trait_property.get_description()
            log.debug("Adding numeric TraitProperty '%s' to header", keyword_name)
            primary_hdu.header[keyword_name] = (
                keyword_value,
                keyword_comment)
        # del keyword_name, keyword_comment, keyword_value

        # Add string value TraitProperties to the primary header
        for trait_property in self.trait_properties(['string']):
            keyword_name = trait_property.get_short_name()
            keyword_value = trait_property.value
            keyword_comment = trait_property.get_description()
            if len(keyword_value) >= 80:
                # This value won't fit, so skip it.
                # @TODO: Issue a warning?
                log.warning("TraitProperty '%s' skipped because it is to long to fit in header", trait_property)
                continue
            log.debug("Adding string TraitProperty '%s' to header", keyword_name)
            primary_hdu.header[keyword_name] = (
                keyword_value,
                keyword_comment)

        # Create extensions for additional record-array-like values (e.g. tabular values)
        # for trait_property in self.trait_property_values('catalog'):
        #     extension = fits.BinTableHDU(trait_property)
        #     hdulist.append(extension)

        hdulist.verify('exception')
        hdulist.writeto(file)

        # If necessary, close the open file handle.
        file_cleanup()
