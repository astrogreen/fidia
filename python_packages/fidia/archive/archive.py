from __future__ import absolute_import, division, print_function, unicode_literals

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

from collections import OrderedDict

import pandas as pd

from ..sample import Sample
from ..traits.utilities import TraitKey, TraitMapping
from .base_archive import BaseArchive

class Archive(BaseArchive):
    def __init__(self):
        # Traits (or properties)
        self.available_traits = TraitMapping()
        self.define_available_traits()
        self._trait_cache = OrderedDict()

        super(BaseArchive, self).__init__()


    def writeable(self):
        raise NotImplementedError("")

    def contents(self):
        return list()

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
        if not isinstance(trait_key, TraitKey) and isinstance(trait_key, tuple):
            trait_key = TraitKey(*trait_key)

        if object_id is not None:
            trait_key = trait_key.replace(object_id=object_id)

        # Check if we have already loaded this trait, otherwise load and cache it here.
        if (trait_key, parent_trait) not in self._trait_cache:

            # Check the size of the cache, and remove item if necessary
            # This should probably be more clever.
            while len(self._trait_cache) > 20:
                self._trait_cache.popitem(last=False)

            # Determine which class responds to the requested trait.
            # Potential for far more complex logic here in future.
            trait_class = self.available_traits[trait_key]

            # Create the trait object and cache it
            log.debug("Returning trait_class %s", type(trait_class))
            trait = trait_class(self, trait_key, parent_trait=parent_trait)

            self._trait_cache[(trait_key, parent_trait)] = trait

        return self._trait_cache[(trait_key, parent_trait)]

    def can_provide(self, trait_key):
        return trait_key in self.available_traits

    def schema(self):
        """Provide a list of trait_keys and classes this archive generally supports."""
        result = dict()
        for trait_type in self.available_traits.get_trait_types():
            result[trait_type] = dict()
            for trait in self.available_traits.get_traits_for_type(trait_type):
                result[trait_type].update(trait.schema())
        return result

    def define_available_traits(self):
        return NotImplementedError()
