from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Type
import fidia

# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports
from fidia.exceptions import *
# from fidia.column import ColumnID
from fidia.base_classes import AbstractBaseTrait
from fidia.traits.trait_key import TraitKey
# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

# __all__ = []

# noinspection PyPep8Naming
class column_reference(object):

    def __init__(self, column_id_or_alias):
        if column_id_or_alias is None:
            raise FIDIAException("a column reference must provide either a column id or an alias.")
        self.column_id_or_alias = column_id_or_alias
        self.column_id = None

    def is_resolved(self):
        return self.column_id is not None



class TraitPointer(object):
    def __init__(self, trait_class=None):
        self._trait_class = None  # type: Type[fidia.Trait]

    @property
    def trait_class(self):
        return self._trait_class

    @trait_class.setter
    def trait_class(self, value):
        assert issubclass(value, AbstractBaseTrait)
        self._trait_class = value  # type: fidia.Trait

    def __getitem__(self, item):
        tk = TraitKey.as_traitkey(item)

        self._trait_class()