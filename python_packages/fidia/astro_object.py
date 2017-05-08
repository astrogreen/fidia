from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List
import fidia

# Python Standard Library Imports
import collections

# Other Library Imports

# FIDIA Imports
import fidia.base_classes as bases
from fidia.utilities import snake_case
# from .traits import TraitKey

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['AstronomicalObject']



class AstronomicalObject:

    def __init__(self, sample, identifier=None, ra=None, dec=None):
        # type: (fidia.Sample, str, float, float) -> None
        if identifier is None:
            if ra is None or dec is None:
                raise Exception("Either 'identifier' or 'ra' and 'dec' must be defined.")
            self._identifier = "J{ra:3.6}{dec:+2.4d}".format(ra=ra, dec=dec)
        else:
            self._identifier = identifier

        # Reference to the sample containing this object.
        self.sample = sample

        # Dictionary of IDs for this object in the various archives attached
        # to the sample. @TODO: Initialised to None: must be populated
        # seperately.
        # self._archive_id = {archive: None for archive in sample.archives}

        self._ra = ra
        self._dec = dec

        # Associate TraitPointer objects as necessary.

        self.update_trait_pointers()

        super(AstronomicalObject, self).__init__()

    @property
    def identifier(self):
        return self._identifier

    @property
    def ra(self):
        return self._ra

    @property
    def dec(self):
        return self._dec

    def update_trait_pointers(self):

        from fidia.traits.references import TraitPointer

        # Clear all existing pointers to TraitPointers
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, bases.TraitPointer):
                delattr(self, attr_name)
        for trait_mapping in self.sample.trait_registry.get_trait_mappings():
            log.debug(trait_mapping.trait_class.trait_class_name)
            pointer_name = snake_case(trait_mapping.trait_class.trait_class_name())
            log.debug("Adding trait pointer %s", pointer_name)
            setattr(self, pointer_name, TraitPointer(self.sample, self, trait_mapping, self.sample.trait_registry))

    def get_archive_id(self, archive):
        return self.sample.get_archive_id(archive, self._identifier)

    def get_feature_catalog_data(self):
        """(Construct) dictionary of featured data from each archive in the sample."""

        feature_data = []

        for archive in self.sample._archives:
            for trait_property_path in archive.feature_catalog_data:
                value = trait_property_path.get_trait_property_value_for_object(self)
                trait = trait_property_path.get_trait_class_for_archive(archive)  # type: fidia.traits.Trait
                tp = trait_property_path.get_trait_property_for_archive(archive)

                # Get the pretty name of the Trait
                pretty_name = trait.get_pretty_name()
                # Append the TraitProperty name only if it is not the default
                if tp.name is not 'value':
                    pretty_name += " " + tp.get_pretty_name()

                # Get the units if present
                unit_string = trait.get_formatted_units()

                feature_data.append({
                    "pretty_name": pretty_name,
                    "value": value,
                    "unit": unit_string,
                    "description": trait.get_description,
                    "trait_key": {
                        "trait_type": trait_property_path[0].trait_type,
                        "trait_qualifier": trait_property_path[0].trait_qualifier,
                        "branch": trait_property_path[0].branch,
                        "version": trait_property_path[0].version
                    }})

        return feature_data


    def keys(self):
        """Provide a list of (presumed) valid TraitKeys for this object"""
        keys = set()
        for ar in self.sample.archives:
            keys.update(ar.available_traits.get_all_traitkeys())


        return keys
