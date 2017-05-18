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

from typing import Dict, List, Type, Union, Tuple
import fidia

# Python Standard Library Imports
from itertools import product
from collections import OrderedDict

# Other Library Imports

# FIDIA Imports
from fidia.exceptions import *
import fidia.base_classes as bases
from .trait_key import TraitKey, validate_trait_name, validate_trait_branch, validate_trait_version
from ..fidiatype import fidia_type
from ..utilities import DefaultsRegistry, SchemaDictionary, is_list_or_set
from .. import exceptions

# Logging import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()





class TraitMappingDatabase(bases.TraitMappingDatabase):

    def __init__(self):
        self.mappings = dict()  # type: Dict[Tuple[str, str], fidia.traits.TraitMapping]
        self.linked_mappings = []  # type: List[TraitMappingDatabase]

    def link_database(self, other_database, index=-1):
        # type: (TraitMappingDatabase, int) -> None
        assert isinstance(other_database, TraitMappingDatabase)
        self.linked_mappings.insert(index, other_database)

    def register_trait_mapping(self, trait_mapping):
        # type: (fidia.traits.TraitMapping) -> None
        if trait_mapping.key() in self.mappings:
            raise FIDIAException("Attempt to add an existing mapping")
        trait_mapping.validate()
        self.mappings[trait_mapping.key()] = trait_mapping

    def register_trait_mapping_list(self, trait_mapping_list):
        # type: (List[fidia.traits.TraitMapping]) -> None

        for mapping in trait_mapping_list:
            self.register_trait_mapping(mapping)

    def get_trait_mappings(self):

        # @TODO: This raises an exception if there are duplicate TraitMapping entries in the system.

        trait_mapping_keys_returned = set()

        for tm in self.mappings.values():
            string_key = "-".join(tm.key())
            if string_key in trait_mapping_keys_returned:
                raise FIDIAException('Duplicate TraitMappings found: %s' % string_key)
            trait_mapping_keys_returned.add(string_key)
            yield tm

        for sub_database in self.linked_mappings:
            for tm in sub_database.mappings.values():
                string_key = "-".join(tm.key())
                if string_key in trait_mapping_keys_returned:
                    raise FIDIAException('Duplicate TraitMappings found: %s' % string_key)
                yield tm
