
# Standard Library Imports
import pickle
import copy
from io import BytesIO
from collections import OrderedDict, Mapping

from contextlib import contextmanager

# Other library imports
from astropy.io import fits
import pandas as pd

# Internal package imports
from ..exceptions import *

from .trait_property import TraitProperty
from .base_trait import Trait
from .trait_key import TraitKey
# This makes available all of the usual parts of this package for use here.
#
# I think this will not cause a circular import because it is a module level import.
# from . import meta_data_traits

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


def trait_property_from_pandas_series(name, data_source):
    # type: (str, pd.Series) -> TraitProperty

    # pd.Series objects have numpy dtypes. Kinds are:
    # http://docs.scipy.org/doc/numpy/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind
    if data_source.dtype.kind in ('i', 'u'):
        tp_type = 'int'
    elif data_source.dtype.kind in ('S', 'U'):
        tp_type = 'string'
    elif data_source.dtype.kind in ('f',):
        tp_type = 'float'
    elif data_source.dtype.kind in ('O',):
        tp_type = 'string'
    else:
        raise ValueError("Source Series must be a float, int, or string type, not '%s'" % data_source.dtype.kind)

    new_trait_property = TraitProperty(name=name, type=tp_type)

    new_trait_property._data_source = data_source  # type: pd.Series

    def loader(trait):
        # type: (Trait) -> Any
        return data_source[trait.object_id]

    new_trait_property.fload = loader

    # Use the series name as the short name
    new_trait_property.set_short_name(data_source.name)

    # # @TODO: Providence information can't get filename currently...
    # tp.providence = "!: FITS-Header {{file: '{filename}' extension: '{extension}' header: '{card_name}'}}".format(
    #     card_name=header_card_name, extension=extension, filename='UNDEFINED'
    # )

    return new_trait_property

def catalog_trait(TraitClass, trait_name, mapping):
    # type: (Trait, str, dict[str, pd.Series]) -> Trait
    class new_trait(TraitClass): pass

    # if hasattr(TraitClass, 'unit'):
    input_unit = mapping.pop('unit', None)

    new_trait.unit = property(lambda: input_unit)

    for key in mapping:
        trait_property = trait_property_from_pandas_series(key, mapping[key])
        setattr(new_trait, key, trait_property)

    new_trait.trait_type, qualifier = TraitKey.split_trait_name(trait_name)
    if qualifier is not None:
        new_trait.qualifiers = {qualifier}
    new_trait.__name__ = "CatalogTrait_" + trait_name
    # new_trait.branches_versions = {trait_key.branch: {trait_key.version}}

    # assert issubclass(new_trait, Trait)

    return new_trait