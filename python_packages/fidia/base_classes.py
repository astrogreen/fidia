"""This module provides all of the base classes used in FIDIA.



"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Any, Iterable, Union, List
import fidia

# Python Standard Library Imports
import collections
from abc import ABCMeta, abstractclassmethod, abstractproperty

# Other Library Imports
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import reconstructor

# FIDIA Imports

# NOTE: This module should not import anything from FIDIA as that would
#       likely to cause a circular import error.

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


# Set up SQL Alchemy in declarative base mode:
SQLAlchemyBase = declarative_base()

class PersistenceBase:
    """A mix in class that adds SQLAchemy database persistence with some extra features."""

    _is_reconstructed = None  # type: bool

    def __init__(self):
        super(PersistenceBase, self).__init__()
        self._is_reconstructed = False

    @reconstructor
    def __db_init__(self):
        self._is_reconstructed = True


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

    trait_mappings = None  # type: TraitMappingDatabase


class AstronomicalObject:
    pass


class Archive(object):

    trait_mappings = None  # type: Union[TraitMappingDatabase, List[TraitMapping]

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

class Mapping:

    def validate(self, recurse=False, raise_exception=False):
        raise NotImplementedError()

    def as_specification_dict(self, columns=None):
        raise NotImplementedError()


class Column:
    def get_value(self, object_id):
        # type: (str) -> Any
        raise NotImplemented()
