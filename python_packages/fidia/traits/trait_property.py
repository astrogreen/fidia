from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Type, Any
import fidia

# Standard Library Imports
import re

# Internal package imports
from fidia.exceptions import *
from ..descriptions import DescriptionsMixin
from ..utilities import RegexpGroup

# Logging import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.enable_console_logging()
log.setLevel(slogging.WARNING)


class TraitProperty(DescriptionsMixin):

    allowed_types = RegexpGroup(
        'string',
        'float',
        'int',
        re.compile(r"string\.array\.\d+"),
        re.compile(r"float\.array\.\d+"),
        re.compile(r"int\.array\.\d+"),
        # # Same as above, but with optional dimensionality
        # re.compile(r"string\.array(?:\.\d+)?"),
        # re.compile(r"float\.array(?:\.\d+)?"),
        # re.compile(r"int\.array(?:\.\d+)?"),
    )

    catalog_types = [
        'string',
        'float',
        'int'
    ]

    non_catalog_types = RegexpGroup(
        re.compile(r"string\.array\.\d+"),
        re.compile(r"float\.array\.\d+"),
        re.compile(r"int\.array\.\d+")
        # # Same as above, but with optional dimensionality
        # re.compile(r"string\.array(?:\.\d+)?"),
        # re.compile(r"float\.array(?:\.\d+)?"),
        # re.compile(r"int\.array(?:\.\d+)?"),
    )

    descriptions_allowed = 'instance'

    def __init__(self, dtype, n_dim=0, optional=False, name=None):
        self.dtype = dtype
        self.n_dim = n_dim
        self.optional = optional
        self.name = name
        self._type = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._type = value

    # noinspection PyProtectedMember
    def __get__(self, trait, trait_class):
        # type: (fidia.Trait, Type[fidia.Trait]) -> Any
        if trait is None:
            return self
        else:
            if self.name is None:
                raise TraitValidationError("TraitProperty not correctly initialised.")
            column_id = trait.trait_schema[self.name]
            result = trait._get_column_data(column_id)
            setattr(trait, self.name, result)
            return result

    def __repr__(self):
        return "<TraitProperty {}>".format(self.name)
