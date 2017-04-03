from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Union, Tuple

# Standard Library imports:
import re
import os
import time
from contextlib import contextmanager
from collections import OrderedDict

# Other library imports:
import numpy as np
import astropy.table as astropy_table
from astropy.io import fits
from cached_property import cached_property

# Internal package imports:
from .base_trait import Trait
from ..utilities import RegexpGroup, is_list_or_set
from ..exceptions import *

# Logging Setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


class ColumnDefinitionList(object):
    def __init__(self, column_definitions=()):

        self._contents = OrderedDict()
        self._contents_by_alias = OrderedDict()
        self._alias_by_id = OrderedDict()

        for coldef in column_definitions:
            self.add(coldef)

    def __getitem__(self, item):
        # type: (str) -> ColumnDefinition
        if item in self._contents_by_alias.keys():
            return self._contents_by_alias[item]
        else:
            return self._contents[item]

    def add(self, coldef):
        # type: (Union[ColumnDefinition, Tuple[str, ColumnDefinition]]) -> None
        log.debug("Adding column definition: %s", coldef)
        if is_list_or_set(coldef):
            log.debug("Column definition is a tuple.")
            if not len(coldef) == 2:
                raise FIDIAException("must be either a column definition or a tuple of (alias, definition)")
            # First item is alias, second item is actual definition
            alias = coldef[0]
            col = coldef[1]
        else:
            log.debug("Column definition is just a ColumnDefinition.")
            col = coldef
            alias = None

        assert isinstance(alias, (str, type(None)))
        assert isinstance(col, (ColumnDefinition, FIDIAColumn))

        if alias:
            self._contents_by_alias[alias] = col
        self._contents[col.id] = col
        self._alias_by_id[col.id] = alias

    def __iter__(self):
        for column_id in self._alias_by_id:
            yield (self._alias_by_id[column_id], self._contents[column_id])

class FIDIAColumn(object):
    """FIDIAColumns represent the atomic data unit in FIDIA.


    The Column is a collection of atomic data for a list/collection of objects
    in a Sample or Archive. The data an element of a column is either an atomic
    python type (string, float, int) or an array of the same, usually as a numpy
    array.

    Columns behave like, and can be used as, astropy.table Columns.


    Implementation Details
    ----------------------

    Currently, this is a direct subclass of astropy.table.Column. However, that
    is in turn a direct subclass of np.ndarray. Therefore, it is not possible to
    create an "uninitialised" Column object that has no data (yet). This will
    cause problems with handling larger data-sets, as we'll have out of memory
    errors. Therefore, it will be necessary to re-implement most of the
    astropy.table.Column interface, while avoiding being a direct sub-class of
    np.ndarray.

    Previously known as TraitProperties

    """

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

    # def __new__(cls, id, data):
    #     self = super(FIDIAColumn, cls).__new__(cls, data=data)
    #
    #     return self

    def __init__(self, *args, **kwargs):

        # Internal storage for data of this column
        self._data = kwargs.pop('data', None)
        self._id = kwargs.pop('id', None)

        # Data Type information
        dtype = kwargs.pop('dtype', None)
        self._dtype = dtype
        fidia_type = kwargs.pop('fidia_type', None)
        self._fidia_type = fidia_type

        # Internal storage for IVOA Uniform Content Descriptor
        self._ucd = kwargs.get('ucd', None)

        # Archive Connection
        self._archive = kwargs.pop('archive', None)
        self._archive_id = kwargs.pop('archive_id', None)

        self._timestamp = kwargs.pop('timestamp', None)
        self._coldef_id = kwargs.pop('coldef_id', None)

    @property
    def id(self):
        return "{archive_id}:{coldef_id}:{timestamp}".format(
            archive_id=self._archive_id,
            coldef_id=self._coldef_id,
            timestamp=self._timestamp
        )

    def __repr__(self):
        return self.id

    # def __get__(self, instance=None, owner=None):
    #     # type: (Trait, Trait) -> str
    #     if instance is None:
    #         return self
    #     else:
    #         if issubclass(owner, Trait):
    #             return self.data[instance.archive_index]

    def associate(self, archive):
        # type: (fidia.archive.archive.Archive) -> None
        try:
            instance_column = super(FIDIAColumn, self).associate(archive)
        except:
            raise
        else:
            instance_column._archive = archive
            instance_column._archive_id = archive.archive_id
        return instance_column


    @property
    def ucd(self):
        return getattr(self, '_ucd', None)

    @ucd.setter
    def ucd(self, value):
        self._ucd = value

    @property
    def type(self):
        """The FIDIA type of the data in this column.

        These are restricted to be those in `FIDIAColumn.allowed_types`.

        Implementation Details
        ----------------------

        Note that it may be preferable to have this property map from the
        underlying numpy type rather than be explicitly set by the user.

        """

        return self._fidia_type

    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._fidia_type = value

    @property
    def archive(self):
        return self._archive

    @archive.setter
    def archive(self, value):
        if self._archive is not None:
            self._archive = value
        else:
            raise AttributeError("archive is already set: cannot be changed.")


class FIDIAArrayColumn(FIDIAColumn):

    def __init__(self, *args, **kwargs):

        self._data = None

        self._ndim = kwargs.pop('ndim', 0)
        self._shape = kwargs.pop('shape', None)

        dtype = kwargs.pop('dtype', None)
        self._dtype = dtype

        super(FIDIAArrayColumn, self).__init__(*args, **kwargs)

    def get_value(self, object_id):
        if self._data is not None:
            return self._data[object_id]
        else:
            raise FIDIAException("Column has no data")

    @property
    def ndarray(self):

        arr = np.empty((len(self._data),) + self._shape, dtype=self._dtype)

        for i, elem in enumerate(self._data.values()):
            arr[i] = elem

        return arr


class ColumnDefinition(object):

    def __init__(self, **kwargs):
        if 'timestamp' in kwargs:
            self._timestamp = kwargs['timestamp']

    @cached_property
    def id(self):
        klass = type(self).__module__ + "." + type(self).__name__
        if hasattr(self, '_id'):
            return klass + ":" + self._id
        return klass + ":" + repr(self)

    def _timestamp_helper(self, archive):
        return None

    def get_timestamp(self, archive=None):
        # type: (Union[None, fidia.archive.archive.Archive]) -> int
        # Option 1: Timestamp has been defined
        if getattr(self, '_timestamp', None):
            log.debug("Timestamp for column %s predefined to be %s", self, self._timestamp)
            return self._timestamp
        # Option 2: A timestamp helper function is defined
        ts = self._timestamp_helper(archive)
        if ts is not None:
            return ts
        # Option 3: Return the current time as the timestamp
        return time.time()

    def associate(self, archive):
        # type: (fidia.archive.archive.Archive) -> FIDIAColumn
        column = self.column_type(
            archive_id=archive.archive_id,
            archive=archive,
            timestamp=self.get_timestamp(archive),
            coldef_id=self.id
        )
        # Call on_associate helpers of any sub-classes:
        if type(self) is not ColumnDefinition:
            super(type(self), self).on_associate(archive, column)

        # Bake in parameters to object_getter function and associate:
        def baked_object_getter(object_id):
            return self.object_getter(archive, object_id)
        column.get_value = baked_object_getter

        log.debug("Created column: %s", column)

        return column

    object_getter = None
    array_getter = None


    def on_associate(self, archive, column):
        pass

class PathBasedColumn:
    """Mix in class to add path based setup to Columns"""

    def __init__(self, *args, **kwargs):
        self.basepath = None


class FITSDataColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAArrayColumn

    def __init__(self, filename_pattern, extension,
                 **kwargs):
        super(FITSDataColumn, self).__init__(**kwargs)
        self.filename_pattern = filename_pattern
        self.fits_extension_identifier = extension

        self._id = "{file}[{ext}]".format(file=filename_pattern, ext=extension)

    def object_getter(self, archive, object_id):
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        with fits.open(full_path_pattern.format(object_id=object_id)) as hdulist:
            return hdulist[self.fits_extension_identifier].data


class FITSHeaderColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAColumn

    def __init__(self, filename_pattern, fits_extension_id, keyword_name,
                 **kwargs):
        super(FITSHeaderColumn, self).__init__(**kwargs)
        self.filename_pattern = filename_pattern
        self.fits_extension_identifier = fits_extension_id
        self.keyword_name = keyword_name

        self._id = "{file}[{ext}].header[{kw}]".format(file=filename_pattern, ext=fits_extension_id, kw=keyword_name)


    def object_getter(self, archive, object_id):
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        with fits.open(full_path_pattern.format(object_id=object_id)) as hdulist:
            return hdulist[self.fits_extension_identifier].header[self.keyword_name]

    def _timestamp_helper(self, archive):
        if archive is None:
            return None
        timestamp = 0
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        for object_id in archive.contents:
            stats = os.stat(full_path_pattern.format(object_id=object_id))
            if stats.st_mtime > timestamp:
                timestamp = stats.st_mtime
        return timestamp

class ColumnFromData(ColumnDefinition):

    def __init__(self, data, **kwargs):
        super(ColumnFromData, self).__init__(**kwargs)
        self._data = data

    @property
    def data(self):
        return self._data


def ArrayColumnFromData(identifier, object_ids, data):
    column = FIDIAArrayColumn()

    column._data = OrderedDict(zip(object_ids, data))

    column._ndim = data[0].ndim

    column._shape = data[0].shape

    column._dtype = data[0].dtype

    return column



class FIDIAColumnGroup:


    def __init__(self):

        # The preload count is used to track how many accesses there are to this
        # trait so that it can be properly cleaned up when all loads are
        # complete.
        self._preload_count = 0

        # Call user provided `init` funciton
        self.init()

    #
    #  __             __             __        ___  __   __     __   ___  __
    # |__) |    |  | / _` | |\ |    /  \ \  / |__  |__) |__) | |  \ |__  /__`
    # |    |___ \__/ \__> | | \|    \__/  \/  |___ |  \ |  \ | |__/ |___ .__/
    #
    # The following three functions are for the "plugin-writter" to override.
    #

    def init(self):
        """Extra initialisations for a Trait.

        Override this function with any extra initialisation required for this
        trait, but not things such as opening files or connecting to a database:
        see `preload` and `cleanup` for those things.

        """
        pass

    def preload(self):
        """Prepare for a trait property to be retrieved using plugin code.

        Override this function with any initialisation required for this trait
        to load its data, such as opening required files, connecting to databases, etc.

        """
        pass

    def cleanup(self):
        """Cleanup after a trait property has been retrieved using plugin code.

        Override this function with any cleanup that should be done once this trait
        to loaded its data, such as closing files.

        """
        pass

    #
    #  __   __   ___       __        __          __
    # |__) |__) |__  |    /  \  /\  |  \ | |\ | / _`
    # |    |  \ |___ |___ \__/ /~~\ |__/ | | \| \__>
    #
    # Methods to handle loading the data associated with this Trait into memory.

    @contextmanager
    def preloaded_context(self):
        """Returns a context manager reference to the preloaded trait, and cleans up afterwards."""
        try:
            # Preload the Trait if necessary.
            self._load_incr()
            log.debug("Context manager version of Trait %s created", self.trait_key)
            yield self
        finally:
            # Cleanup the Trait if necessary.
            self._load_decr()
            log.debug("Context manager version of Trait %s cleaned up", self.trait_key)

    def _load_incr(self):
        """Internal function to handle preloading. Prevents a Trait being loaded multiple times.

        This function should be called prior to anything which requires calling
        TraitProperty loaders, typically only by the TraitProperty object
        itself.

        See also the `preloaded_context` function.
        """
        log.vdebug("Incrementing preload for trait %s", self.trait_key)
        assert self._preload_count >= 0
        try:
            if self._preload_count == 0:
                self.preload()
        except:
            log.exception("Exception in preloading trait %s", self.trait_key)
            raise
        else:
            self._preload_count += 1

    def _load_decr(self):
        """Internal function to handle cleanup.

        This function should be called after anything which requires calling
        TraitProperty loaders, typically only by the TraitProperty object
        itself.
        """
        log.vdebug("Decrementing preload for trait %s", self.trait_key)
        assert self._preload_count > 0
        try:
            if self._preload_count == 1:
                self.cleanup()
        except:
            raise
        else:
            self._preload_count -= 1
