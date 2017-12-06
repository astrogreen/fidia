"""

Column Definitions
------------------

This module handles defining columns of data for access in FIDIA.

:class:`.ColumnDefinition` objects define columns of data, and how the data can
be accessed. An :class:`.ArchiveDefinition` contains a list of column
definitions: `.ArchiveDefinition.columns`. When the corresponding :class:`.Archive` is
created, these column definitions are converted into actual :class:`.FIDIAColumn`
objects (which are defined in :mod:`fidia.columns.columns`).


"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Union, Tuple, Dict, Type
import fidia

# Python Standard Library Imports
import os
import re
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
from ..exceptions import FIDIAException, DataNotAvailable
from .columns import FIDIAColumn, FIDIAArrayColumn, PathBasedColumn, ColumnID
from ..utilities import is_list_or_set

# Set up logging
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['ColumnDefinitionList', 'ColumnDefinition',
           'FITSDataColumn', 'FITSHeaderColumn', 'FITSBinaryTableColumn',
           'CSVTableColumn',
           'SQLColumn',
           'RawFileColumn',
           'SourcelessColumn', 'FixedValueColumn']

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
    _id_param_re = None

    _parameters = []

    _meta_kwargs = ('dtype', 'n_dim', 'unit', 'ucd')
    _desc_kwargs = ('pretty_name', 'short_description', 'long_description')


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
        self.short_description = kwargs.pop('short_description', "")
        self.long_description = kwargs.pop('long_description', "")

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

        # Prepare the column id:
        id_string_format = self._id_string.format(**{param: arg for arg, param in zip(args, self._parameters)})
        log.vdebug(repr(id_string_format))
        self._id = id_string_format.replace(":", "_")
        log.vdebug(repr(self._id))

    @classmethod
    def from_id(cls, id_string):
        assert ":" not in id_string, "id_string should be the column name portion of the column ID only."
        if cls._id_param_re is None:
            cls._id_param_re = re.sub(r"\\{([A-Za-z0-9_]+)\\}", r"(?P<\1>.+)", re.escape(cls._id_string))
            log.debug("Regular expression for column name inferred: %s", cls._id_param_re)
        match = re.fullmatch(cls._id_param_re, id_string)

        if match is None:
            raise ValueError("column name provided could not be parsed.")

        return cls(*[match.groupdict()[param] for param in cls._parameters])


    @cached_property
    def id(self):
        """The column part of a full column ID."""
        klass = self.class_name()
        if hasattr(self, '_id'):
            log.vdebug(repr(self._id))
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
        try:
            self.unit = unit.to_string("vounit")
        except ValueError as e:
            # @TODO: VOUnit in astropy.units should better support logrythmic units in future.
            if str(e).startswith("Function units cannot be written in vounit format") or \
                    str(e).startswith("Unit 'dex' is not part of the VOUnit standard"):
                self.unit = unit.to_string()
            else:
                raise
        log.debug("Unit created: %s", self.unit)

    def __repr__(self):
        return (self.__class__.__name__ + "(" +
                ", ".join([repr(getattr(self, attr)) for attr in self._parameters]) + ", " +
                ", ".join([kw + "=" + repr(getattr(self, kw)) for kw in self._meta_kwargs]) + ", " +
                ",\n ".join([kw + "=" + repr(getattr(self, kw)) for kw in self._desc_kwargs]) +
                ")")

    def __str__(self):
        """Prints a representation of the column with its ID."""
        return "FIDIAColumn(" + self.id + ")"

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

        2. The timestamp determined by the helper function :func:`._timestamp_helper`

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
        try:
            ts = self._timestamp_helper(archive)
        except:
            log.warning("Exception occurred while calling `%s._timestamp_helper", self.__class__.__name__)
            if log.isEnabledFor(slogging.DEBUG):
                log.exception()
            pass
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
            coldef_id=self.id,
            short_description=self.short_description,
            long_description=self.long_description,
            pretty_name=self.pretty_name
        )
        assert isinstance(column, FIDIAColumn)
        # assert hasattr(column, "archive_id")
        # assert column.id.archive_id
        # Call on_associate helpers of any sub-classes:
        if type(self) is not ColumnDefinition:

            # Note, this next line appears to be an invalid reference, but it
            # actually refers to super-classes only of sub-classes of this
            # class, so it really refers to `self.on_associate` (which is
            # defined). This code is not visited if we are not a subclass of
            # ColumnDefinition

            # noinspection PyUnresolvedReferences
            super(type(self), self).on_associate(archive, column)

        # Copy the object_getter and array_getters onto the output column if
        # present.
        #
        # When the functions are copied, attributes required from the archive
        # instance are copied here so that database persistence will not need to
        # Pickle the archive to store the getters.

        if hasattr(self, 'object_getter'):
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

        if hasattr(self, 'array_getter'):
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

    def on_associate(self, archive, column):
        pass


#  __   __                           __   ___  ___          ___    __        __
# /  ` /  \ |    |  |  |\/| |\ |    |  \ |__  |__  | |\ | |  |  | /  \ |\ | /__`
# \__, \__/ |___ \__/  |  | | \|    |__/ |___ |    | | \| |  |  | \__/ | \| .__/
#

def get_fits_extension_by_name_or_index(hdulist, extension):
    """Helper function that will parse string indexes of FITS extensions to integer indexes if necessary."""
    try:
        return hdulist[extension]
    except KeyError as key_error:
        try:
            idx = int(extension)
        except:
            # Simply raise the error that astropy.io.fits raised:
            raise key_error
        else:
            return hdulist[idx]

# noinspection PyUnresolvedReferences
class FITSDataColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAArrayColumn
    _id_string = "{filename_pattern}[{extension}]"
    _parameters = ("filename_pattern", "extension")

    # noinspection PyMethodOverriding
    def object_getter(self, object_id, basepath):
        # Signature of this function differs from base class: see column definition documentation
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with fits.open(full_path_pattern.format(object_id=object_id)) as hdulist:
            hdu = get_fits_extension_by_name_or_index(hdulist, self.extension)
            return hdu.data


# noinspection PyUnresolvedReferences
class FITSHeaderColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAColumn
    _id_string = "{filename_pattern}[{fits_extension_id}].header[{keyword_name}]"
    _parameters = ('filename_pattern', 'fits_extension_id', 'keyword_name')

    # noinspection PyMethodOverriding
    def object_getter(self, object_id, basepath):
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with fits.open(full_path_pattern.format(object_id=object_id)) as hdulist:
            # return hdulist[self.fits_extension_id].header[self.keyword_name]
            hdu = get_fits_extension_by_name_or_index(hdulist, self.fits_extension_id)
            return hdu.header[self.keyword_name]

    def _timestamp_helper(self, archive):
        if archive is None:
            return None
        timestamp = 0
        log.debug("archive.basepath: %s, filename_pattern: %s", archive.basepath, self.filename_pattern)
        full_path_pattern = os.path.join(archive.basepath, self.filename_pattern)
        for object_id in archive.contents:
            try:
                stats = os.stat(full_path_pattern.format(object_id=object_id))
            except FileNotFoundError:
                # Ignore objects where this file is not available (in effect handle as though "DataNotAvailable")
                pass
            else:
                if stats.st_mtime > timestamp:
                    timestamp = stats.st_mtime
        return timestamp

# noinspection PyUnresolvedReferences
class FITSBinaryTableColumn(ColumnDefinition, PathBasedColumn):

    column_type = FIDIAColumn
    _id_string = "{filename_pattern}[{fits_extension_id}].data[{index_column_name}->{column_name}]"
    _parameters = ("filename_pattern", "fits_extension_id", "column_name", "index_column_name")

    def array_getter(self, basepath):
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with fits.open(full_path_pattern) as hdulist:
            hdu = get_fits_extension_by_name_or_index(hdulist, self.fits_extension_id)
            column_data = hdu.data[self.column_name]
            # force native byteorder (https://pandas.pydata.org/pandas-docs/stable/gotchas.html#byte-ordering-issues)
            native_column_data = column_data.byteswap().newbyteorder()
            index = hdu.data[self.index_column_name]
            return pd.Series(native_column_data, index=index, name=self._id, copy=True)

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


class SQLColumn(ColumnDefinition):
    """A column sourced from an SQL database.

    When executed on the given database, the SQL should return exactly two
    columns: a column called 'id' containing the object ID and a column called
    'data' containing data.

    """

    # @TODO: This Column type needs tests, which require SQL data be added to the test data.
    # Note there is an example in `poc/fidia/gama_archive_poc.py`

    column_type = FIDIAColumn

    _id_string = "{select_stmt}"
    # Note: Colons in the database_url will be replaced with underscores in producing the actual id.

    _parameters = ['select_stmt']

    def object_getter(self, object_id, database_url):

        # Requires SQLAlchemy
        from sqlalchemy.sql import column, text, select, Select
        from sqlalchemy import create_engine


        # Note, it would be preferrable to store a single connection on the
        # Archive instance, rather than recreating it here. This can be fixed
        # after ASVO-1089 has been implemented.
        # @TODO: Change to use connection associated with the archive.

        engine = create_engine(database_url)

        connection = engine.connect()

        stmt = text(self.select_stmt).columns(column('id'), column('data')).alias('st')

        # query = select(stmt).where(stmt.c.id == object_id)
        query = select([stmt], from_obj=stmt).where(stmt.c.id == object_id)

        result = connection.execute(query)

        row = result.fetchone()

        return row["data"]

# noinspection PyUnresolvedReferences
class RawFileColumn(ColumnDefinition, PathBasedColumn):
    """RawFileColumns provides access to the raw bytes of a set of files.

    Understanding the structure of the data is left to other places (so a Trait
    that is using a RawFileColumn must know how to interpret the data in that
    column.

    """
    column_type = FIDIAArrayColumn
    _id_string = "{filename_pattern}"
    _parameters = ["filename_pattern"]

    def object_getter(self, object_id, basepath):
        # NOTE: Signature of this function differs from base class: see column definition documentation
        full_path_pattern = os.path.join(basepath, self.filename_pattern)
        with open(full_path_pattern.format(object_id=object_id), 'rb') as fh:
            return fh.read()


# noinspection PyUnresolvedReferences
class SourcelessColumn(ColumnDefinition):
    """A column of data which cannot retrieve it's own data—data must come from the DAL.

    Columns of this type must have their data provided by the Data Access Layer,
    otherwise they will raise a DataNotAvailable exception.

    This column type is largely useful only for prototyping Trait Mapping
    schemas, and for use in cases where the data will always be provided by the
    data access layer.

    """

    column_type = FIDIAColumn
    _id_string = "{description}"
    _parameters = ['description']

    def object_getter(self, object_id):
        raise DataNotAvailable()

# noinspection PyUnresolvedReferences
class FixedValueColumn(ColumnDefinition):
    """A column which returns a single fixed value in all cases.

    The value must be pickleable.

    Probably mostly useful for testing.

    """

    column_type = FIDIAColumn
    _id_string = "{value}"
    _parameters = ['value']

    def object_getter(self, object_id):
        return self.value
