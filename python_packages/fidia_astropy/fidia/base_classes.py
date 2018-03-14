"""This module provides all of the base classes used in FIDIA."""

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


class Sample:
    def archive_for_column(self, column_id):
        # type: (str) -> Archive
        raise NotImplementedError()

    def find_column(self, column_id):
        # type: (str) -> Column
        raise NotImplementedError()

    def get_archive_id(self, archive, sample_id):
        # type (Archive, str) -> str
        raise NotImplementedError()

    # trait_mappings = None  # type: TraitMapping

    contents = None  # type: List[str]

    def __getitem__(self, item):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def keys(self):
        raise NotImplementedError()

    def trait_mappings(self):
        raise NotImplementedError()


class AstronomicalObject:
    pass


class Archive(object):

    trait_mappings = None  # type: Union[TraitMappingDatabase, List[TraitMapping]

    # @property
    # def contents(self):
    #     raise NotImplementedError("")


class BaseTrait:
    pass

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
