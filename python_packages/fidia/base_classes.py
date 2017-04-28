"""This module provides all of the base classes used in FIDIA.



"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Any, Iterable
import fidia

# Python Standard Library Imports
import collections
from abc import ABCMeta, abstractclassmethod, abstractproperty

# Other Library Imports

# FIDIA Imports

# NOTE: This module should not import anything from FIDIA as that would
#       likely to cause a circular import error.

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


class Sample(collections.MutableMapping):
    def archive_for_column(self, column_id):
        # type: (str) -> Archive
        raise NotImplemented()

    def find_column(self, column_id):
        # type: (str) -> Column
        raise NotImplemented()

    def get_archive_id(self, archive, sample_id):
        # type (Archive, str) -> str
        raise NotImplemented()

    trait_registry = None  # type: TraitRegistry


class AstronomicalObject:
    pass


class Archive(object):

    def writeable(self):
        raise NotImplemented()

    # @property
    # def contents(self):
    #     raise NotImplementedError("")

    def get_full_sample(self):
        raise NotImplemented()

    def get_trait(self, object_id=None, trait_key=None, parent_trait=None):
        raise NotImplemented()


class BaseTrait:

    def schema(cls):
        raise NotImplemented()

    def value(self):
        raise NotImplemented()


class Trait(BaseTrait):
    pass

class TraitCollection(BaseTrait):
    pass

class TraitKey:
    pass

class TraitPointer:
    pass


class TraitRegistry:

    def get_trait_mappings(self):
        # type: () -> Iterable[fidia.traits.TraitMapping]
        raise NotImplemented()

class TraitMapping:
    pass


class Column:
    def get_value(self, object_id):
        # type: (str) -> Any
        raise NotImplemented()
