"""

Column Definitions
------------------

This module handles defining columns of data for access in FIDIA.

:class:`.ColumnDefinition` objects define columns of data, and how the data can
be accessed. An :class:`.ArchiveDefinition` contains a list of column
definitions: `.ArchiveDefinition.columns`. When the corresponding :class:`.Archive` is
created, these column definitions are converted into actual :class:`.FIDIAColumn`
objects (which are defined in :module:`~fidia.columns.columns`).


"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Union, Tuple, Dict, Type
import fidia

# Python Standard Library Imports
import os
import time
from collections import OrderedDict
import inspect

# Other Library Imports
import pandas as pd
from astropy.io import fits
from astropy.io import ascii
from astropy import units
from cached_property import cached_property

# FIDIA Imports
from ..exceptions import FIDIAException
from .columns import FIDIAColumn, FIDIAArrayColumn, PathBasedColumn, ColumnID
from ..utilities import is_list_or_set

# Set up logging
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['ColumnDefinitionList', 'ColumnDefinition',
           'FITSDataColumn', 'FITSHeaderColumn', 'FITSBinaryTableColumn',
           'CSVTableColumn']

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
        raise KeyError("Unknown column ID %s" % item)

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

    def extend(self, list):
        for item in list:
            self.add(item)

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

    _id_string = ""

    _parameters = []

    _meta_kwargs = ('dtype', 'n_dim', 'unit', 'ucd')
    _desc_kwargs = ('pretty_name', 'short_desc', 'long_desc')


    def __init__(self, *args, **kwargs):
        # self._parameters = []
        # for name, param in inspect.signature(self.__init__).parameters.items():
        #     if param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
        #         self._parameters.append(name)
        # self._parameters = [param.name
        #                     for param in inspect.signature(self.__init__).parameters.values()
        #                     if param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD]
        for arg, param in zip(args, self._parameters):
            setattr(self, param, arg)

        if 'timestamp' in kwargs:
            self._timestamp = kwargs['timestamp']

        self.dtype = kwargs.pop('dtype', str)
        self.n_dim = kwargs.pop('n_dim', 0)

        self.pretty_name = kwargs.pop('pretty_name', "")
        self.short_desc = kwargs.pop('short_desc', "")
        self.long_desc = kwargs.pop('long_desc', "")

        unit = kwargs.pop('unit', None)
        if isinstance(unit, units.Unit):
            self._unit = unit
            self.unit = unit.to_string("vounit")
        elif unit is None:
            # If the unit isn't available/hasn't been provided, we store it as
            # None/NULL, which is distinct from the empty string "", which is
            # interpreted as a dimensionless unit.
            #
            # This requires special handling wherever the astropy.units package comes into play.
            self.unit = self._unit = unit
        else:
            self.unit = unit

        self.ucd = kwargs.pop('ucd', "")

        self._id = self._id_string.format(
            **{param: arg for arg, param in zip(args, self._parameters)}
        )

    @cached_property
    def id(self):
        """The column part of a full column ID."""
        klass = self.class_name()
        if hasattr(self, '_id'):
            return ":".join((klass, self._id))
        return ":".join((klass, repr(self)))

    @classmethod
    def class_name(cls):
        # type: () -> str
        """Determine the class-name of the ColumnDefinition.

        If the column definition is part of FIDIA, then this is the bare class.
        If not, then it includes the module path to the class.

        """
        klass = cls.__module__ + "." + cls.__name__
        if klass.startswith('fidia.'):
            klass = cls.__name__
        return klass

    def _validate_unit(self):
        if self.unit is not None and isinstance(getattr(self, '_unit', None), units.UnitBase):
            # Unit has already been validated, no further action required
            return
        if self.unit is None:
            # This column has no units, so no further action required
            return
        log.debug("Attempting to create unit for '%s'", self.unit)
        try:
            # noinspection PyTypeChecker
            unit = units.Unit(self.unit)  # , format="vounit", parse_strict='raise')
            # @TODO: Astropy units doesn't correctly validate when the format is 'vounit'.
            # See https://github.com/astropy/astropy/issues/6302
        except:
            if log.isEnabledFor(slogging.DEBUG):
                log.exception("unit creation unsuccessful")
            raise
        if isinstance(unit, units.UnrecognizedUnit):
            raise units.UnitsError("Unrecognized unit %s" % unit)
        self._unit = unit
        self.unit = unit.to_string("vounit")
        log.debug("Unit created: %s", self.unit)

    def __repr__(self):
        return (self.__class__.__name__ + "(" +
                ", ".join([repr(getattr(self, attr)) for attr in self._parameters]) + ", " +
                ", ".join([kw + "=" + repr(getattr(self, kw)) for kw in self._meta_kwargs]) + ", " +
                ",\n ".join([kw + "=" + repr(getattr(self, kw)) for kw in self._desc_kwargs]) +
                ")")

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

            # Note, this next line appears to be an invalid reference, but it
            # actually refers to super-classes only of sub-classes of this
            # class, so it really refers to `self.on_associate` (which is
            # defined). This code is not visited if we are not a subclass of
            # ColumnDefinition

            # noinspection PyUnresolvedReferences
            super(type(self), self).on_associate(archive, column)

        # Copy the object_getter and array_getters onto the output column
        #
        # This is only done if the corresponding functions have actually been
        # overridden, as determined by the `.is_implemented` property.
        #
        # When the functions are copied, attributes required from the archive
        # instance are copied here so that database persistence will not need to
        # Pickle the archive to store the getters.

        if getattr(self.object_getter, 'is_implemented',True):
            log.debug("Copying object_getter function from ColumnDefinition %s to new Column", self)
            # Bake in parameters to object_getter function and associate:
            sig = inspect.signature(self.object_getter)
            baked_args = dict()
            for archive_attr in sig.parameters.keys():
                if archive_attr is 'object_id':
                    # Don't process the object_id parameter as an archive attribute.
                    continue
                baked_args[archive_attr] = getattr(archive, archive_attr)

            column._object_getter = self.object_getter
            column._object_getter_args = baked_args

        if getattr(self.array_getter, 'is_implemented', True):
            log.debug("Copying array_getter function from ColumnDefinition %s to new Column", self)
            # Bake in parameters to object_getter function and associate:
            sig = inspect.signature(self.array_getter)
            baked_args = dict()
            for archive_attr in sig.parameters.keys():
                baked_args[archive_attr] = getattr(archive, archive_attr)
            column._array_getter = self.array_getter
            column._array_getter_args = baked_args

        log.debug("Created column: %s", str(column))

        return column

    def object_getter(self, object_id):
        """Method to get data in this column for a single object.
        
        When this column definition is used to create a `.FIDIAColumn`, this
        function is included if defined. See `ColumnDefinition.associate`.
        
        """
        raise NotImplementedError()
    # We define an extra property on this function below, which allows the
    # 'associate' function above to determine if it has been overridden. If it
    # hasn't, it shouldn't be copied onto the FIDIAColumn instance.
    object_getter.is_implemented = False

    def array_getter(self, object_id):
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


# noinspection PyUnresolvedReferences
class FITSDataColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAArrayColumn

    _id_string = "{filename_pattern}[{extension}]"

    _parameters = ("filename_pattern", "extension")

    # def __init__(self, filename_pattern, extension,
    #              **kwargs):
    #     super(FITSDataColumn, self).__init__(filename_pattern, extension, **kwargs)

    # def __init__(self, filename_pattern, extension,
    #              **kwargs):
    #     super(FITSDataColumn, self).__init__(**kwargs)
    #     self.filename_pattern = filename_pattern
    #     self.extension = extension
    #
    #     self._id = "{file}[{ext}]".format(file=filename_pattern, ext=extension)

    # noinspection PyMethodOverriding
    def object_getter(self, object_id, basepath):
        # Signature of this function differs from base class: see column definition documentation
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with fits.open(full_path_pattern.format(object_id=object_id)) as hdulist:
            return hdulist[self.extension].data


# noinspection PyUnresolvedReferences
class FITSHeaderColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAColumn

    _id_string = "{filename_pattern}[{fits_extension_id}].header[{keyword_name}]"

    _parameters = ('filename_pattern', 'fits_extension_id', 'keyword_name')

    # def __init__(self, filename_pattern, fits_extension_id, keyword_name, **kwargs):
    #     super(FITSHeaderColumn, self).__init__(filename_pattern, fits_extension_id, keyword_name, **kwargs)
        # super(FITSHeaderColumn, self).__init__(**kwargs)
        # self.filename_pattern = filename_pattern
        # self.fits_extension_identifier = fits_extension_id
        # self.keyword_name = keyword_name
        #
        # self._id = "{file}[{ext}].header[{kw}]".format(file=filename_pattern, ext=fits_extension_id, kw=keyword_name)


    # noinspection PyMethodOverriding
    def object_getter(self, object_id, basepath):
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with fits.open(full_path_pattern.format(object_id=object_id)) as hdulist:
            return hdulist[self.fits_extension_id].header[self.keyword_name]

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

# noinspection PyUnresolvedReferences
class FITSBinaryTableColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAColumn

    _id_string = "{filename_pattern}[{fits_extension_id}].data[{column_name}]"

    _parameters = ("filename_pattern", "fits_extension_id", "column_name", "index_column_name")

    # def __init__(self, filename_pattern, fits_extension_id, column_name, index_column_name,
    #              **kwargs):
    #     super(FITSBinaryTableColumn, self).__init__(**kwargs)
    #     self.filename_pattern = filename_pattern
    #
    #     if fits_extension_id == 0:
    #         raise FIDIAException("FITSBinaryTableColumn cannot use extension 0. Perhaps you want 1?")
    #     self.fits_extension_identifier = fits_extension_id
    #
    #     self.column_name = column_name
    #
    #     self.index_column_name = index_column_name
    #
    #     self._id = "{file}[{ext}].data[{kw}]".format(file=filename_pattern, ext=fits_extension_id, kw=column_name)


    def array_getter(self, basepath):
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with fits.open(full_path_pattern) as hdulist:
            column_data = hdulist[self.fits_extension_id].data[self.column_name]
            index = hdulist[self.fits_extension_id].data[self.index_column_name]
            return pd.Series(column_data, index=index, name=self._id, copy=True)

    def _timestamp_helper(self, archive):
        if archive is None:
            return None
        log.debug("archive.basepath: %s, filename_pattern: %s", archive.basepath, self.filename_pattern)
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        stats = os.stat(full_path_pattern)
        timestamp = stats.st_mtime
        return timestamp

# noinspection PyUnresolvedReferences
class CSVTableColumn(ColumnDefinition, PathBasedColumn):
    column_type = FIDIAColumn
    _id_string = "{filename_pattern}[{index_column_name}->{column_name}](comment={comment})"
    _parameters = ('filename_pattern', 'column_name', 'index_column_name', 'comment')

    def array_getter(self, basepath):
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        table = ascii.read(full_path_pattern, format="csv", comment=self.comment)

        assert self.column_name in table.colnames
        assert self.index_column_name in table.colnames

        column_data = table[self.column_name].data
        index = table[self.index_column_name].data
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