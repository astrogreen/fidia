"""

Column Definitions
------------------

This module handles defining columns of data for access in FIDIA.

:class:`.ColumnDefinition` objects define columns of data, and how the data can
be accessed. An :class:`.Archive` definition, a list of column definitions is
provided. When that :class:`.Archive` is loaded, these column definitions are converted
into actual :class:`.FIDIAColumn` objects (which are defined in
:module:`~fidia.columns.columns`).


"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Union, Tuple, Dict
import fidia

# Python Standard Library Imports
import os
import time
from collections import OrderedDict

# Other Library Imports
import pandas as pd
from astropy.io import fits
from cached_property import cached_property

# FIDIA Imports
from ..exceptions import FIDIAException
from .columns import FIDIAColumn, FIDIAArrayColumn, PathBasedColumn, ColumnID, ColumnIDDict
from ..utilities import is_list_or_set

# Set up logging
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['ColumnDefinitionList', 'ColumnDefinition',
           'FITSDataColumn', 'FITSHeaderColumn', 'FITSBinaryTableColumn']

class ColumnDefinitionList(object):
    def __init__(self, column_definitions=()):

        self._contents = OrderedDict()  # type: Dict[ColumnID, Union[ColumnDefinition, FIDIAColumn]]
        self._contents_by_alias = OrderedDict()  # type: Dict[str, Union[ColumnDefinition, FIDIAColumn]]
        self._alias_by_id = OrderedDict()  # type: Dict[ColumnID, str]

        for coldef in column_definitions:
            self.add(coldef)

    def __getitem__(self, item):
        # type: (str) -> Union[ColumnDefinition, FIDIAColumn]
        if item in self._contents_by_alias.keys():
            return self._contents_by_alias[item]
        if item in self._contents:
            return self._contents[item]
        log.warning("ColumnID '%s' not in %s", item, self)

    def add(self, coldef):
        # type: (Union[Union[ColumnDefinition, FIDIAColumn], Tuple[str, Union[ColumnDefinition, FIDIAColumn]]]) -> None
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

    def __repr__(self):
        coldefs = ""
        for id in self._contents:
            if coldefs != "":
                coldefs += ",\n "
            coldefs += "({alias}, '{id}')".format(
                alias=repr(self._alias_by_id[id]),
                id=str(id)
            )
        return "ColumnDefinitionList((\n" + coldefs + "\n))"

class ColumnDefinition(object):
    """Base class for Column Definitions.

    All Column Definition classes should be based on this class.

    This class provides:

    column id handling
        Column IDs are central to FIDIA's design, and enable code based on it to be
        portable between different computers/systems/environments.


    """

    column_type = None  # type: Type[FIDIAColumn]

    def __init__(self, **kwargs):
        if 'timestamp' in kwargs:
            self._timestamp = kwargs['timestamp']

    @cached_property
    def id(self):
        """The column part of a full column ID."""
        klass = type(self).__module__ + "." + type(self).__name__
        if klass.startswith('fidia.'):
            klass = type(self).__name__
        if hasattr(self, '_id'):
            return ":".join((klass, self._id))
        return ":".join((klass, repr(self)))

    def _timestamp_helper(self, archive):
        # type: (fidia.archive.archive.Archive) -> Union[None, int, float]
        """A helper function that subclasses can override to change how the column timestamp is determined.

        This function is called as needed by :function:`.get_timestamp`.

        Parameters
        ----------
        archive : Archive
            The Archive instance that the column is to be defined on.


        """
        return None

    def get_timestamp(self, archive=None):
        # type: (Union[None, fidia.archive.archive.Archive]) -> int
        """Determine the timestamp for this column.

        The timestamp is determined by considering (in order) the following sources:

        1. An explicitly provided timestamp when the column was defined:

            >>> col = ColumnDefinition(timestamp=34)
            >>> col.get_timestamp()
            34

        2. The timestamp determined by the helper function :function:`._timestamp_helper`

        3. The current time.

        Parameters
        ----------
        archive : Archive (optional)
            An archive instance, which will be passed to `_timestamp_helper` if necessary.

        """
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
        # type: (fidia.Archive) -> FIDIAColumn
        """Convert a column definition defined on an `Archive` class into a `FIDIAColumn` on an archive instance.
        
        This function is effectively a factory for `.FIDIAColumn` instances. In
        addition to calling the constructor, it also sets either the
        `.object_getter` function or the `.array_getter` function, or both.
        These functions are copies of the corresponding functions on this
        `ColumnDefinition` class, but have a pointer to the archive instance
        "built in".
        
        """
        if self.column_type is None or not issubclass(self.column_type, FIDIAColumn):
            raise FIDIAException("Column Definition validation error: column_type must be defined.")
        column = self.column_type(
            archive_id=archive.archive_id,
            archive=archive,
            timestamp=self.get_timestamp(archive),
            coldef_id=self.id
        )
        assert isinstance(column, FIDIAColumn)
        # Call on_associate helpers of any sub-classes:
        if type(self) is not ColumnDefinition:
            super(type(self), self).on_associate(archive, column)

        # Copy the object_getter and array_getters onto the output column
        #
        # This is only done if the corresponding functions have actually been
        # overridden, as determined by the `.is_implemented` property.
        #
        # When the functions are copied, a pointer to the archive is "baked in"
        # so that the function no longer requires the archive as an argument.
        if getattr(self.object_getter, 'is_implemented',True):
            log.debug("Copying object_getter function from ColumnDefinition %s to new Column", self)
            # Bake in parameters to object_getter function and associate:
            def baked_object_getter(object_id):
                return self.object_getter(archive, object_id)
            column.get_value = baked_object_getter
            # Note: `baked_object_getter` is a static method, so it will only be
            # passed one argument when invoked.
        if getattr(self.array_getter, 'is_implemented', True):
            log.debug("Copying array_getter function from ColumnDefinition %s to new Column", self)
            # Bake in parameters to object_getter function and associate:
            def baked_array_getter():
                column._data = self.array_getter(archive)
            column.get_array = baked_array_getter
            # Note: `baked_array_getter` is a static method, so it will only be
            # passed one argument when invoked.

        log.debug("Created column: %s", str(column))

        return column

    def object_getter(self, archive, object_id):
        """Method to get data in this column for a single object.
        
        When this column definition is used to create a `.FIDIAColumn`, this
        function is included if defined. See `ColumnDefinition.associate`.
        
        """
        raise NotImplementedError()
    # We define an extra property on this function below, which allows the
    # 'associate' function above to determine if it has been overridden. If it
    # hasn't, it shouldn't be copied onto the FIDIAColumn instance.
    object_getter.is_implemented = False

    def array_getter(self, archive, object_id):
        """Method to get data in this column for a single object.

        When this column definition is used to create a `.FIDIAColumn`, this
        function is included if defined. See `ColumnDefinition.associate`.

        """
        raise NotImplementedError()
    # We define an extra property on this function below, which allows the
    # 'associate' function above to determine if it has been overridden. If it
    # hasn't, it shouldn't be copied onto the FIDIAColumn instance.
    array_getter.is_implemented = False


    def on_associate(self, archive, column):
        pass


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
        log.debug("archive.basepath: %s, filename_pattern: %s", archive.basepath, self.filename_pattern)
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        for object_id in archive.contents:
            stats = os.stat(full_path_pattern.format(object_id=object_id))
            if stats.st_mtime > timestamp:
                timestamp = stats.st_mtime
        return timestamp

class FITSBinaryTableColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAColumn

    def __init__(self, filename_pattern, fits_extension_id, column_name, index_column_name,
                 **kwargs):
        super(FITSBinaryTableColumn, self).__init__(**kwargs)
        self.filename_pattern = filename_pattern

        if fits_extension_id == 0:
            raise FIDIAException("FITSBinaryTableColumn cannot use extension 0. Perhaps you want 1?")
        self.fits_extension_identifier = fits_extension_id

        self.column_name = column_name

        self.index_column_name = index_column_name

        self._id = "{file}[{ext}].data[\"{kw}\"]".format(file=filename_pattern, ext=fits_extension_id, kw=column_name)


    def array_getter(self, archive):
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        with fits.open(full_path_pattern) as hdulist:
            column_data = hdulist[self.fits_extension_identifier].data[self.column_name]
            index = hdulist[self.fits_extension_identifier].data[self.index_column_name]
            return pd.Series(column_data, index=index, name=self._id, copy=True)

    def _timestamp_helper(self, archive):
        if archive is None:
            return None
        log.debug("archive.basepath: %s, filename_pattern: %s", archive.basepath, self.filename_pattern)
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        stats = os.stat(full_path_pattern)
        timestamp = stats.st_mtime
        return timestamp


class ColumnFromData(ColumnDefinition):

    def __init__(self, data, **kwargs):
        super(ColumnFromData, self).__init__(**kwargs)
        self._data = data

    @property
    def data(self):
        return self._data