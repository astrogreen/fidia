from __future__ import absolute_import, division, print_function, unicode_literals

# Standard Library imports:
import re
import os
from contextlib import contextmanager
from collections import OrderedDict

# Other library imports:
import numpy as np
import astropy.table as astropy_table
from astropy.io import fits
from cached_property import cached_property

# Internal package imports:
from .base_trait import Trait
from ..utilities import RegexpGroup
from ..exceptions import *

# Logging Setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

class FIDIAColumn(astropy_table.Column):
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

    def __new__(cls, id, data):
        self = super(FIDIAColumn, cls).__new__(cls, data=data)

        return self

    def __init__(self, *args, **kwargs):

        # Internal storage for IVOA Uniform Content Descriptor
        self._ucd = None

    def __get__(self, instance=None, owner=None):
        # type: (Trait, Trait) -> str
        if instance is None:
            return self
        else:
            if issubclass(owner, Trait):
                return self.data[instance.archive_index]

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

        return self._type
    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._type = value

class FIDIAArrayColumn:

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


    def __init__(self, *args, **kwargs):

        self._data = None

        self._ndim = kwargs.pop('ndim', 0)
        self._shape = kwargs.pop('shape', None)

        dtype = kwargs.pop('dtype', None)
        self._dtype = dtype

        # Internal storage for IVOA Uniform Content Descriptor
        self._ucd = kwargs.get('ucd', None)

    def get_value(self, object_id):
        if self._data is not None:
            return self._data[object_id]
        else:
            raise FIDIAException("Column has no data")

    def __get__(self, instance=None, owner=None):
        # type: (Trait, Trait) -> str
        if instance is None:
            return self
        else:
            if issubclass(owner, Trait):
                return self._data[instance.object_id]

    @property
    def ucd(self):
        return getattr(self, '_ucd', None)

    @ucd.setter
    def ucd(self, value):
        self._ucd = value

    @property
    def ndarray(self):

        arr = np.empty((len(self._data),) + self._shape, dtype=self._dtype)

        for i, elem in enumerate(self._data.values()):
            arr[i] = elem

        return arr

    @property
    def type(self):
        """The FIDIA type of the data in this column.

        These are restricted to be those in `FIDIAColumn.allowed_types`.

        Implementation Details
        ----------------------

        Note that it may be preferable to have this property map from the
        underlying numpy type rather than be explicitly set by the user.

        """

        return self._type
    @type.setter
    def type(self, value):
        if value not in self.allowed_types:
            raise Exception("Trait property type '{}' not valid".format(value))
        self._type = value


class FITSDataColumn(FIDIAArrayColumn):

    def __init__(self, filename_pattern, extension,
                 **kwargs):
        super(FITSDataColumn, self).__init__(**kwargs)
        self.basepath = None
        self.filename_pattern = filename_pattern
        self.extension = extension

        self.archive = None
        self.archive_id = None

    @cached_property
    def fullpath_pattern(self):
        if self.basepath is None:
            raise AttributeError("The basepath must be defined first.")
        return os.path.join(self.basepath, self.filename_pattern)

    def associate_with_archive(self, archive):
        self.archive = archive  # type: fidia.Archive
        self.archive_id = archive.name
        self.basepath = archive.basepath

    def get_value(self, object_id):
        if self.archive_id is None:
            raise FIDIAException("Column not associated with an archive: cannot retrieve data.")
        with fits.open(self.fullpath_pattern.format(object_id=object_id)) as hdulist:
            return hdulist[self.extension].data

def ColumnFromData(identifier, object_ids, data):

    column = FIDIAColumn(data=data, id=identifier)
    column._index = object_ids
    return column

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
