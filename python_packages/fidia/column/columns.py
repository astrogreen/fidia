from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Union, Callable
import fidia

# Python Standard Library Imports
import re
from contextlib import contextmanager
from operator import itemgetter, attrgetter
from collections import OrderedDict
import types

# Other Library Imports
import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection, mapped_collection

# FIDIA Imports
import fidia.base_classes as bases
from ..exceptions import FIDIAException, DataNotAvailable
from ..utilities import RegexpGroup

# Set up logging
from fidia import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


# noinspection PyInitNewSignature
class ColumnID(str):
    """ColumnID(archive_id, column_type, column_name, timestamp)"""

    # @TODO: More tests required of this.

    __slots__ = ('archive_id', 'column_type', 'column_name', 'timestamp')

    def __new__(cls, string):
        # @TODO: Validation
        self = str.__new__(cls, string)
        split = string.split(":")
        if len(split) == 2:
            # Only column type and name
            self.archive_id = None
            self.column_type = split[0]
            self.column_name = split[1]
            self.timestamp = None
            return self
        if len(split) == 4:
            # Fully defined
            self.archive_id = split[0]
            self.column_type = split[1]
            self.column_name = split[2]
            self.timestamp = split[3]
            return self
        if len(split) == 1:
            # Column name contains no colons, so assume it is not a `proper'
            # ColumnID and just populate the name
            self.archive_id = None
            self.column_type = None
            self.column_name = string
            self.timestamp = None
            return self
        raise ValueError("Supplied string cannot be parsed as a ColumnID: %s" % string)

    @classmethod
    def as_column_id(cls, key):
        # type: (Union[str, tuple, ColumnID]) -> ColumnID
        """Return a ColumnID for the given input.

        Effectively this is just a smart "cast" from string or tuple.

        """
        if isinstance(key, ColumnID):
            return key
        if isinstance(key, tuple):
            return cls(":".join(key))
        if isinstance(key, str):
            return cls(key)
        raise KeyError("Cannot parse ID '{}' into a ColumnID".format(key))

    @property
    def type(self):
        """Determine how much information is available in this ColumnID.

        Returns
        -------

        'short': Only `.column_type` and `.column_name` are defined

        'full': Fully defined ColumnID

        'non-conformant': Cases of arbitrary strings with no colons. Only `.column_name` is defined.

        'unknown': Some other situation is present (possibly a programming error).

        """
        
        if (self.archive_id is None and
                self.column_type is not None and
                self.column_name is not None and
                self.timestamp is None):
            return 'short'
        if (self.archive_id is not None and
                self.column_type is not None and
                self.column_name is not None and
                self.timestamp is not None):
            return 'full'
        if (self.archive_id is None and
                self.column_type is None and
                self.column_name is not None and
                self.timestamp is None):
            return 'non-conformant'
        return 'unknown'

    def __repr__(self):
        """Return a nicely formatted representation string"""
        return 'ColumnID(%s)' % super(ColumnID, self).__repr__()

    # def _asdict(self):
    #     """Return a new OrderedDict which maps field names to their values"""
    #     return collections.OrderedDict(zip(self._fields, self))

    def replace(self, **kwargs):
        """Return a new ColumnID object replacing specified fields with new values"""
        result = ColumnID.as_column_id(map(kwargs.pop, self.__slots__, self.as_tuple))
        if kwargs:
            raise ValueError('Got unexpected field names: %r' % kwargs.keys())
        return result

    # def __str__(self):
    #     string = self.column_name
    #     if self.column_type:
    #         string = self.column_type + ":" + string
    #     if self.timestamp:
    #         string = string + ":" + str(self.timestamp)
    #     if self.archive_id:
    #         string = self.archive_id + ":" + string
    #     assert isinstance(string, str)
    #     return string

    def as_dict(self):
        split = self.split(":")
        if len(split) == 2:
            # Only column type and name
            return {'column_type': split[0], 'column_name': split[1]}
        if len(split) == 4:
            # Fully defined
            return {'archive_id': split[0], 'column_type': split[1], 'column_name': split[2], 'timestamp': split[3]}

    def as_tuple(self):
        return tuple(map(attrgetter, self.__slots__))


class ColumnIDDict(OrderedDict):

    def timestamps(self, column_id):
        column_id = ColumnID.as_column_id(column_id)
        for key in self.keys():
            if key.replace(timestamp=None) == column_id.replace(timestamp=None):
                yield key.timestamp
    
    def latest_timestamp(self, column_id):
        return max(self.timestamps(column_id))

    def __getitem__(self, item):
        column_id = ColumnID.as_column_id(item)

        if column_id.timestamp != 'latest':
            return super(ColumnIDDict, self).__getitem__(column_id)
        else:
            latest_timestamp = self.latest_timestamp(column_id)
            return super(ColumnIDDict, self).__getitem__(column_id.replace(timestamp=latest_timestamp))



class FIDIAColumn(bases.PersistenceBase, bases.SQLAlchemyBase):
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

    __tablename__ = "fidia_columns"  # Note this table is shared with FIDIAArrayColumn subclass
    _database_id = sa.Column(sa.Integer, sa.Sequence('column_seq'), primary_key=True)

    # Polymorphism (subclasses stored in same table)
    _db_type = sa.Column('type', sa.String(50))
    __mapper_args__ = {'polymorphic_on': "_db_type", 'polymorphic_identity': 'FIDIAColumn'}

    # Relationships (foreign keys)
    _db_archive_id = sa.Column(sa.Integer, sa.ForeignKey("archives._db_id"))
    # trait_property_mappings = relationship("TraitPropertyMapping", back_populates="_trait_mappings",
    #                                        collection_class=attribute_mapped_collection('name'))  # type: Dict[str, TraitPropertyMapping]
    _archive = relationship("Archive")  # type: fidia.Archive

    # Storage Columns
    _column_id = sa.Column(sa.String)
    _object_getter = sa.Column(sa.PickleType)  # type: Callable
    _object_getter_args = sa.Column(sa.PickleType)
    _array_getter = sa.Column(sa.PickleType)  # type: Callable
    _array_getter_args = sa.Column(sa.PickleType)

    # Column Meta-data storage
    _ucd = sa.Column(sa.String)
    _unit = sa.Column(sa.String)
    _dtype = sa.Column(sa.String)
    pretty_name = sa.Column(sa.UnicodeText(length=30))
    short_description = sa.Column(sa.Unicode(length=150))
    long_description = sa.Column(sa.UnicodeText)

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
        """Create a new FIDIAColumn. This should only be called by `ColumnDefinition.associate`.



        """
        super(FIDIAColumn, self).__init__()

        # Internal storage for data of this column
        self._data = kwargs.pop('data', None)

        # Data Type information. Parsing and validation already done by `ColumnDefinition`.
        self._dtype = kwargs.pop('dtype', None)

        # Internal storage for IVOA Uniform Content Descriptor
        self._ucd = kwargs.get('ucd', None)

        # Unit information
        self._unit = kwargs.get('unit', None)

        # Archive Connection
        # self._archive = kwargs.pop('archive', None)  # type: fidia.Archive
        self._archive_id = kwargs.pop('archive_id', None)

        # Construct the ID
        self._timestamp = kwargs.pop('timestamp', None)
        self._coldef_id = kwargs.pop('coldef_id', None)
        if "column_id" in kwargs:
            self._column_id = kwargs["column_id"]
            log.debug("Column ID Provided: %s", self._column_id)
        elif (self._archive_id is not None and
              self._timestamp is not None and
              self._coldef_id is not None):
            self._column_id = "{archive_id}:{coldef_id}:{timestamp}".format(
                archive_id=self._archive_id,
                coldef_id=self._coldef_id,
                timestamp=self._timestamp)
            log.debug("Column ID constructed: %s", self._column_id)
        else:
            raise ValueError("Either column_id or all of (archive_id, coldef_id and timestamp) must be provided.")

        # Descriptive meta-data
        self.pretty_name = kwargs.pop("pretty_name")
        self.short_description = kwargs.pop("short_description")
        self.long_description = kwargs.pop("long_description")


    @reconstructor
    def __db_init__(self):
        super(FIDIAColumn, self).__db_init__()
        self._data = None

    @property
    def column_definition_class(self):
        # type: () -> fidia.ColumnDefinition

        # c.f. fidia.utilities.fidia_classname() and fidia.ColumnDefinition.class_name()

        class_name = self.id.column_type
        if "." in class_name:
            # This is a ColumnDefinition defined outside of FIDIA
            raise ValueError("Columns can not retrieve ColumnDefinitions defined outside of FIDIA")
        import fidia.column.column_definitions
        klass = getattr(fidia.column.column_definitions, class_name)
        return klass

    @property
    def id(self):
        # type: () -> ColumnID
        return ColumnID.as_column_id(self._column_id)

    def __repr__(self):
        return str(self.id)

    # def __get__(self, instance=None, owner=None):
    #     # type: (Trait, Trait) -> str
    #     if instance is None:
    #         return self
    #     else:
    #         if issubclass(owner, Trait):
    #             return self.data[instance.archive_index]

    # def associate(self, archive):
    #     # type: (fidia.archive.archive.Archive) -> None
    #     try:
    #         instance_column = super(FIDIAColumn, self).associate(archive)
    #     except:
    #         raise
    #     else:
    #         instance_column._archive = archive
    #         instance_column._archive_id = archive.archive_id
    #     return instance_column


    def get_value(self, object_id, provenance="any"):
        """Retrieve the value from this column for the given object ID.


        Implementation
        --------------

        This function tries each of the following steps until one returns a value:

        1. Search the Data Access Layer
        2. Use original `ColumnDefinition.object_getter` stored in local `._object_getter`
        3. Use original `ColumnDefinition.array_getter` stored in local `._array_getter`, selecting just this row.

        """

        if provenance not in ['any', 'dal', 'definition']:
            raise ValueError("provenance must be one of 'any', 'dal' or 'definition'")

        if provenance in ['any', 'dal']:
            # STEP 1: Search the data access layer
            try:
                return fidia.dal_host.search_for_cell(self, object_id)
            except:
                log.info("DAL did not provide data for column_id %s, object_id %s", self.id, object_id, exc_info=True)

        if provenance in ['any', 'definition']:

            # Confirm that at least one getter is available from the definition
            if self._object_getter is None and self._array_getter is None:
                raise FIDIAException("No getter functions available for column")

            # STEP 2: Use original `ColumnDefinition.object_getter`
            log.debug("Column '%s' retrieving value for object %s using original definitions", self, object_id)
            if self._object_getter is not None:
                log.vdebug("Retrieving using cell getter from ColumnDefinition")
                log.vdebug("_object_getter(object_id=\"%s\", %s)", object_id, self._object_getter_args)
                result = self._object_getter(object_id, **self._object_getter_args)
                assert result is not None, "ColumnDefinition.object_getter must not return `None`."
                return result

            #  STEP 3: Use original `ColumnDefinition.array_getter`
            log.vdebug("Retrieving using array getter from ColumnDefinition via `._default_get_value`")
            return self._default_get_value(object_id)

        # This should not be reached unless something is wrong with the state of the data/ingestion.
        raise DataNotAvailable("Neither the DAL nor the original ColumnDefinition could provide the requested data.")

    def get_array(self):
        if self._array_getter is not None:
            result = self._array_getter(**self._array_getter_args)
            assert result is not None, "ColumnDefinition.array_getter must not return `None`."
            assert isinstance(result, pd.Series)
            ordered_result = result.reindex(self.contents, copy=False)
            # Since `copy=False`, this will only do work if required, otherwise the original Series is returned.
            #   see: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.reindex.html
            # @NOTE: The order of self.contents is not preserved from how it is initialized.
            return ordered_result
        else:
            data = []
            index = []
            for object_id in self.contents:
                try:
                    data.append(self.get_value(object_id))
                except DataNotAvailable:
                    # This row of the array has no data. To avoid causing
                    # up-casting of the type, (from e.g. int to float to
                    # accomodate np.nan), we simply don't add this row to the
                    # pd.Series object.
                    pass
                else:
                    index.append(object_id)
                    # @NOTE: It may be more efficient to copy the index and then
                    # remove items, rather than building it up.
            series = pd.Series(data, index=index)
            if series.dtype.name != self._dtype:
                raise TypeError("get_array constructed an array of the wrong type %s, should be %s for column %s" %
                                (series.dtype.name, self._dtype, self))
            return series


    def _default_get_value(self, object_id):
        """Individual value getter, takes object_id as argument.

        Notes
        -----

        The implementation here is not necessarily used. When a ColumnDefinition
        is associated with an archive, the resulting Column object typically has
        get_value replaced with a version based on the `.object_getter` defined
        on the ColumnDefinition.

        See `ColumnDefinition.associate()`.

        """
        if self._data is not None:
            assert isinstance(self._data, pd.Series)
            return self._data.at[object_id]
        elif self.get_array is not None:
            self._data = self.get_array()
            # assert self._data is not None, "Programming Error: get_array should populate _data"
            return self._data[object_id]
        raise FIDIAException("Column has no data")

    @property
    def ucd(self):
        return getattr(self, '_ucd', None)

    @ucd.setter
    def ucd(self, value):
        self._ucd = value

    @property
    def unit(self):
        return self._unit

    @property
    def timestamp(self):
        if getattr(self, '_timestamp', None):
            return self._timestamp
        else:
            if "." in self.id.timestamp:
                return float(self.id.timestamp)
            else:
                return int(self.id.timestamp)

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
    def contents(self):
        return self._archive.contents

    # @property
    # def archive(self):
    #     return self._archive
    #
    # @archive.setter
    # def archive(self, value):
    #     if self._archive is not None:
    #         self._archive = value
    #     else:
    #         raise AttributeError("archive is already set: cannot be changed.")


class FIDIAArrayColumn(FIDIAColumn):

    __mapper_args__ = {'polymorphic_identity': 'FIDIAArrayColumn'}

    def __init__(self, *args, **kwargs):

        self._data = None

        self._ndim = kwargs.pop('ndim', 0)
        self._shape = kwargs.pop('shape', None)

        dtype = kwargs.pop('dtype', None)
        self._dtype = dtype

        super(FIDIAArrayColumn, self).__init__(*args, **kwargs)

    @property
    def ndarray(self):

        arr = np.empty((len(self._data),) + self._shape, dtype=self._dtype)

        for i, elem in enumerate(self._data.values()):
            arr[i] = elem

        return arr


class PathBasedColumn:
    """Mix in class to add path based setup to Columns"""

    def __init__(self, *args, **kwargs):
        self.basepath = None

