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
from ..exceptions import FIDIAException
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
            self.column_type = split[0]
            self.column_name = split[1]
        if len(split) == 4:
            # Fully defined
            self.archive_id = split[0]
            self.column_type = split[1]
            self.column_name = split[2]
            self.timestamp = split[3]
        return self

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

        super(FIDIAColumn, self).__init__()

        # Internal storage for data of this column
        self._data = kwargs.pop('data', None)

        # Data Type information
        # dtype = kwargs.pop('dtype', None)
        # self._dtype = dtype

        # Internal storage for IVOA Uniform Content Descriptor
        # self._ucd = kwargs.get('ucd', None)

        # Archive Connection
        # self._archive = kwargs.pop('archive', None)  # type: fidia.Archive
        self._archive_id = kwargs.pop('archive_id', None)

        # Construct the ID
        self._timestamp = kwargs.pop('timestamp', None)
        self._coldef_id = kwargs.pop('coldef_id', None)
        if "column_id" in kwargs:
            self._column_id = kwargs["column_id"]
        elif (self._archive_id is not None and
              self._timestamp is not None and
              self._coldef_id is not None):
            self._column_id = "{archive_id}:{coldef_id}:{timestamp}".format(
                archive_id=self._archive_id,
                coldef_id=self._coldef_id,
                timestamp=self._timestamp)
        else:
            raise ValueError("Either column_id or all of (archive_id, coldef_id and timestamp) must be provided.")


    @reconstructor
    def __db_init__(self):
        super(FIDIAColumn, self).__db_init__()
        self._data = None


    @property
    def id(self):
        return self._column_id

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

    def get_value(self, object_id):
        log.debug("Column '%s' retrieving value for object %s", self, object_id)
        if self._object_getter is not None:
            log.vdebug("Retrieving using cell getter from ColumnDefinition")
            log.vdebug("_object_getter(object_id=\"%s\", %s)", object_id, self._object_getter_args)
            return self._object_getter(object_id, **self._object_getter_args)
        elif self._array_getter is not None:
            log.vdebug("Retrieving using array getter from ColumnDefinition via `._default_get_value`")
            return self._default_get_value(object_id)
        else:
            raise FIDIAException("No getter functions available for column")

    def get_array(self):
        if self._array_getter is not None:
            return self._array_getter(**self._array_getter_args)
        else:
            raise FIDIAException("No array getter function available for column")

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