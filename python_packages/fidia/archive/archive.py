from __future__ import absolute_import, division, print_function, unicode_literals

from .. import slogging
log = slogging.getLogger(__name__)
# log.setLevel(slogging.DEBUG)
log.enable_console_logging()

from collections import OrderedDict

import pandas as pd

from ..sample import Sample
from ..traits import Trait, TraitKey, TraitProperty
from ..traits import TraitRegistry
from .base_archive import BaseArchive
from ..cache import DummyCache
from ..utilities import SchemaDictionary
from ..exceptions import *

class Archive(BaseArchive):
    def __init__(self):
        # Traits (or properties)
        self.available_traits = TraitRegistry()
        self.define_available_traits()
        self._trait_cache = OrderedDict()

        self.cache = DummyCache()

        self._schema = {'by_trait_type': None, 'by_trait_name': None}

        super(BaseArchive, self).__init__()


    def writeable(self):
        raise NotImplementedError("")

    @property
    def contents(self):
        return self._contents
    @contents.setter
    def contents(self, value):
        self._contents = set(value)


    @property
    def name(self):
        raise NotImplementedError("")

    def get_full_sample(self):
        """Return a sample containing all objects in the archive."""
        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        new_sample = Sample()
        id_cross_match = pd.DataFrame(pd.Series(map(str, self.contents), name=self.name, index=self.contents))

        # For a new, empty sample, extend effectively just copies the id_cross_match into the sample's ID list.
        new_sample.extend(id_cross_match)

        # Add this archive to the set of archives associated with the sample.
        new_sample._archives = {self}

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        return new_sample

    def get_trait(self, object_id=None, trait_key=None, parent_trait=None):

        if trait_key is None:
            raise ValueError("The TraitKey must be provided.")
        if object_id is None:
            raise ValueError("The object_id must be provided.")
        trait_key = TraitKey.as_traitkey(trait_key)

        # Fill in default values for any `None`s in `TraitKey`
        trait_key = self.available_traits.update_key_with_defaults(trait_key)

        # Check if we have already loaded this trait, otherwise load and cache it here.
        if (object_id, trait_key, parent_trait) not in self._trait_cache:

            # Check the size of the cache, and remove item if necessary
            # This should probably be more clever.
            while len(self._trait_cache) > 20:
                self._trait_cache.popitem(last=False)

            # Determine which class responds to the requested trait.
            # Potential for far more complex logic here in future.
            trait_class = self.available_traits.retrieve_with_key(trait_key)

            # Create the trait object and cache it
            log.debug("Returning trait_class %s", type(trait_class))
            trait = trait_class(self, trait_key, object_id=object_id, parent_trait=parent_trait)

            self._trait_cache[(object_id, trait_key, parent_trait)] = trait

        return self._trait_cache[(object_id, trait_key, parent_trait)]

    def type_for_trait_path(self, path):
        """Return the type for the provided Trait path.

        :param path:
            A sequence object containing the pieces of the "path" addressing the
            object of interest.

        This function is a shortcut to determine what kind of object one should
        expect if requesting a particular Trait or trait property as defined by
        the path provided. This is a shortcut, i.e., the Traits are not actually
        constructed. It shouldn't be considered absolutely authoritative, but
        should be close.

        Currently, this can only differentiate between a Trait and a Trait Property.
        This could be made more specific in one of several ways:

        - Have the schema include type information when it is constructed.
        - Find the appropriate class by querying the TraitMapping object
          at each level.

        """

        # Drill down the schema:
        schema = self.schema(by_trait_name=True)
        current_schema_item = schema
        for path_element in path:
            trait_key = TraitKey.as_traitkey(path_element)
            current_schema_item = current_schema_item[trait_key.trait_name]

        # Decide whether the item in the schema corresponds to a Trait or TraitProperty
        if isinstance(current_schema_item, dict):
            return Trait
        else:
            return TraitProperty

    def can_provide(self, trait_key):
        return trait_key.trait_name in self.available_traits.get_trait_names()

    def schema(self, by_trait_name=False):
        """Provide a list of trait_keys and classes this archive generally supports."""

        if by_trait_name:
            # Produce a version of the schema which has trait_type and
            # trait_name combined on a single level.
            if self._schema['by_trait_name']:
                # Cached copy available, return that.
                return self._schema['by_trait_name']
            result = SchemaDictionary()
            log.debug("Building a schema by_trait_name for archive '%s'", self)
            for trait_name in self.available_traits.get_trait_names():
                log.debug("    Processing traits with trait_name '%s'", trait_name)
                result[trait_name] = SchemaDictionary()
                for trait in self.available_traits.get_traits(trait_name_filter=trait_name):
                    log.debug("        Attempting to add Trait class '%s'", trait)
                    trait_schema = trait.schema(by_trait_name=by_trait_name)
                    try:
                        result[trait_name].update(trait_schema)
                    except ValueError:
                        log.error("Schema mis-match in traits: trait '%s' cannot be added " +
                                  "to schema for '%s' containing: '%s'",
                                  trait, trait_name, result[trait_name])
                        raise SchemaError("Schema mis-match in traits")
            self._schema['by_trait_name'] = result

        else:
            # Produce a version of the schema which has trait_type on one level,
            # and trait_name on the next nested level.
            if self._schema['by_trait_type']:
                # Cached copy available, return that.
                return self._schema['by_trait_type']
            result = SchemaDictionary()
            log.debug("Building a schema by_trait_type for archive '%s'", self)
            trait_types = self.available_traits.get_trait_types()
            for trait_type in trait_types:
                log.debug("    Processing traits with trait_type '%s'", trait_type)
                result[trait_type] = SchemaDictionary()
                trait_names = self.available_traits.get_trait_names(trait_type_filter=trait_type)
                for trait_name in trait_names:
                    log.debug("        Processing traits with trait_name '%s'", trait_name)
                    trait_qualifier = TraitKey.split_trait_name(trait_name)[1]
                    for trait in self.available_traits.get_traits(trait_name_filter=trait_name):
                        log.debug("            Attempting to add Trait class '%s'", trait)
                        trait_schema = trait.schema(by_trait_name=by_trait_name)
                        if trait_qualifier not in result[trait_type]:
                            result[trait_type][trait_qualifier] = SchemaDictionary()
                        try:
                            result[trait_type][trait_qualifier].update(trait_schema)
                        except ValueError:
                            log.exception("Schema mis-match in traits: trait '%s' cannot be added " +
                                      "to schema for '%s' containing: '%s'",
                                      trait, trait_type, result[trait_type][trait_name])
                            raise SchemaError("Schema mis-match in traits")
                self._schema['by_trait_type'] = result
        return result

    def define_available_traits(self):
        return NotImplementedError()
