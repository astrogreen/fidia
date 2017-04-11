from __future__ import absolute_import, division, print_function, unicode_literals

# Python Standard Library Imports
import re
from contextlib import contextmanager
from operator import itemgetter

# Other Library Imports
import numpy as np

# FIDIA Imports
from ..exceptions import FIDIAException
from ..utilities import RegexpGroup

# Set up logging
from fidia import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()



class ColumnID(tuple):
    """ColumnID(archive_id, column_type, column_name, timestamp)"""

    # Originally, this class was created using the following command:
    #     TraitKey = collections.namedtuple('TraitKey', ['trait_type', 'trait_name', 'object_id'], verbose=True)


    __slots__ = ()

    _fields = ('archive_id', 'column_type', 'column_name', 'timestamp')

    def __new__(cls, archive_id, column_type, column_name, timestamp):
        """Create new instance of TraitKey(trait_type, trait_qualifier, branch, version)"""
        # @TODO: Validation
        return tuple.__new__(cls, (archive_id, column_type, column_name, timestamp))

    # @classmethod
    # def _make(cls, iterable, new=tuple.__new__, len=len):
    #     """Make a new TraitKey object from a sequence or iterable"""
    #     result = new(cls, iterable)
    #     if len(result) not in (1, 2, 3, 4):
    #         raise TypeError('Expected 1-4 arguments, got %d' % len(result))
    #     return result

    @classmethod
    def as_column_id(cls, key):
        """Return a ColumnID for the given input.

        Effectively this is just a smart "cast" from string or tuple.

        """
        # if isinstance(key, TraitKey):
        #     return key
        # if isinstance(key, tuple):
        #     return cls(*key)
        # if isinstance(key, str):
        #     match = TRAIT_KEY_RE.fullmatch(key)
        #     if match:
        #         return cls(trait_type=match.group('trait_type'),
        #             trait_qualifier=match.group('trait_qualifier'),
        #             branch=match.group('branch'),
        #             version=match.group('version'))
        #     match = TRAIT_KEY_ALT_RE.fullmatch(key)
        #     if match:
        #         return cls(trait_type=match.group('trait_type'),
        #             trait_qualifier=match.group('trait_qualifier'),
        #             branch=match.group('branch'),
        #             version=match.group('version'))
        raise KeyError("Cannot parse ID '{}' into a ColumnID".format(key))

    def __repr__(self):
        """Return a nicely formatted representation string"""
        return 'TraitKey(archive_id=%r, column_type=%r, column_name=%r, timestamp=%r)' % self

    # def _asdict(self):
    #     """Return a new OrderedDict which maps field names to their values"""
    #     return collections.OrderedDict(zip(self._fields, self))

    # def replace(_self, **kwds):
    #     """Return a new TraitKey object replacing specified fields with new values"""
    #     result = _self._make(map(kwds.pop, ('trait_type', 'trait_qualifier', 'branch', 'version'), _self))
    #     if kwds:
    #         raise ValueError('Got unexpected field names: %r' % kwds.keys())
    #     return result

    def ashyphenstr(self):
        s = self.trait_type
        if self.trait_qualifier or self.branch or self.version:
            s += "-"
            if self.trait_qualifier:
                s += self.trait_qualifier
            if self.branch or self.version:
                s += "-"
                if self.branch:
                    s += self.branch
                if self.version:
                    s += "-" + self.version
        return s

    def __getnewargs__(self):
        """Return self as a plain tuple.  Used by copy and pickle."""
        return tuple(self)

    # __dict__ = property(_asdict)

    def __getstate__(self):
        """Exclude the OrderedDict from pickling"""
        pass

    def __str__(self):
        trait_string = self.trait_type
        if self.trait_qualifier:
            trait_string += "-" + self.trait_qualifier
        if self.branch:
            trait_string += ":" + self.branch
        if self.version:
            trait_string += "(" + self.version + ")"
        return trait_string

    archive_id = property(itemgetter(0), doc='ID of the Archive providing this column')

    column_type = property(itemgetter(1), doc='class of the corresponding column definition')

    column_name = property(itemgetter(2), doc='name of the column')

    timestamp = property(itemgetter(3), doc='timestamp')




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