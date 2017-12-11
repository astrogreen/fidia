from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Any
import fidia

# Python Standard Library Imports
import os
import pickle
import time
import inspect
from itertools import chain

# Other Library Imports
import numpy as np
import pandas as pd

# FIDIA Imports
from fidia.column import ColumnID, FIDIAArrayColumn
from fidia.exceptions import *
import fidia.column.column_definitions as fidiacoldefs

# Other modules within this package
from ._dal_internals import *

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.INFO)
log.enable_console_logging()

# __all__ = ['Archive', 'KnownArchives', 'ArchiveDefinition']



class NumpyFileStore(DataAccessLayer):
    """A data access layer that stores it's data in Numpy savefiles (`.npy`) and pickled Pandas `pandas.Series` objects.

    Parameters
    ----------
    base_path: str
        Directory to store/find the data in. All of the "cached" data is
        below this directory, which must already exist (even if no data has
        been ingested yet).

    Notes
    -----

    The data is stored in a directory structure with multiple levels. These
    levels reflect the levels of the ColumnID's stored. They are:

    1. Archive ID
    2. ColumnDefinition class name (type)
    3. Column name. NOTE: in many cases the Column Name may contain path
       separator characters already (e.g. for FITS column types). These
       separators are left as is, so there may be more than one directory
       levels at this level.
    4. Timestamp

    Within the directory defined by ColumnID as above, there is either one
    file (for regular FIDIAColumns) or one file per object (for array data
    in FIDIAArrayColumns).


    """

    def __init__(self, base_path):

        if not os.path.isdir(base_path):
            raise FileNotFoundError(base_path + " does not exist.")

        self.base_path = base_path

    # def __repr__(self):
    #     return "NumpyFileStore(base_path={})".format(self.base_path)

    def get_value(self, column, object_id):
        # type: (fidia.FIDIAColumn, str) -> Any
        """Overrides :meth:`DataAccessLayer.get_value`"""

        data_dir = self.get_directory_for_column_id(column.id)

        if not os.path.exists(data_dir):
            raise DALDataNotAvailable("NumpyFileStore has no data for ColumnID %s" % column.id)

        if isinstance(column, FIDIAArrayColumn):
            # Data is in array format, and therefore each cell is stored as a separate file.
            data_path = os.path.join(data_dir, object_id + ".npy")
            data = np.load(data_path)

        else:
            # Data is individual values, so is stored in a single pickled pandas series

            # NOTE: This is loading the entire column into memory to return a
            # single value. This should perhaps instead raise an exception that
            # instructs the caller to use `get_array` instead.

            data_path = os.path.join(data_dir, "pandas_series.pkl")

            with open(data_path, "rb") as f:
                series = pickle.load(f)  # type: pd.Series

            data = series[object_id]

        # Sanity checks that data loaded matches expectations
        assert data is not None

        return data

    def ingest_column(self, column):
        # type: (fidia.FIDIAColumn) -> None
        """Overrides :meth:`DataAccessLayer.ingest_column`"""

        data_dir = self.get_directory_for_column_id(column.id, True)

        if isinstance(column, FIDIAArrayColumn):
            # Data is in array format, and therefore each cell is stored as a separate file.
            # @TODO: If the column definition defines only get_array, this will be badly inefficient?
            for object_id in column.contents:
                try:
                    data = column.get_value(object_id, provenance='definition')
                except:
                    log.warning("No data ingested for object '%s' in column '%s'", object_id, column.id)
                    pass
                else:
                    self.ingest_object_with_data(column, object_id, data)
        else:
            # Data is individual values, so is stored in a single pickled pandas series

            data_path = os.path.join(data_dir, "pandas_series.pkl")

            data = column.get_array()
            log.debug(type(data))
            series = pd.Series(data, index=column.contents)
            series.to_pickle(data_path)

    def ingest_object_with_data(self, column, object_id, data):
        # type: (fidia.FIDIAColumn, str, Any) -> None

        data_dir = self.get_directory_for_column_id(column.id, True)

        if isinstance(column, FIDIAArrayColumn):
            # Data is in array format, and therefore each cell is stored as a separate file.
            data_path = os.path.join(data_dir, object_id + ".npy")
            np.save(data_path, data, allow_pickle=False)
        else:
            raise DALIngestionError("NumpyFileStore.ingest_object_with_data() works only for array data.")

    def ingest_column_with_data(self, column, data):

        data_dir = self.get_directory_for_column_id(column.id, True)

        if isinstance(column, FIDIAArrayColumn):
            # Array column
            raise Exception("Not Implemented")
        else:
            data_path = os.path.join(data_dir, "pandas_series.pkl")
            if isinstance(data, pd.Series):
                series = data
            else:
                series = pd.Series(data, index=column.contents)
            series.to_pickle(data_path)

    def by_object_group_pre_ingestion_callback(self, object_id, grouping_context):
        self.start_size = get_size(self.base_path)
        self.start_time = time.time()

    def by_object_group_post_ingestion_callback(self, object_id, grouping_context):
        delta_time = time.time() - self.start_time
        delta_size = get_size(self.base_path) - self.start_size

        log.info("Ingested Grouped columns %s for object %s",
                 grouping_context, object_id)
        log.info("Ingested %s MB in %s seconds, rate %s Mb/s",
                 delta_size / 1024 ** 2, delta_time, delta_size / 1024 ** 2 / delta_time)

    def by_column_group_pre_ingestion_callback(self, grouping_context):
        self.start_size = get_size(self.base_path)
        self.start_time = time.time()

    def by_column_group_post_ingestion_callback(self, grouping_context):
        delta_time = time.time() - self.start_time
        delta_size = get_size(self.base_path) - self.start_size

        log.info("Ingested Grouped columns %s",
                 grouping_context)
        log.info("Ingested %s MB in %s seconds, rate %s Mb/s",
                 delta_size / 1024 ** 2, delta_time, delta_size / 1024 ** 2 / delta_time)

    def simple_pre_ingestion_callback(self, column):
        self.start_size = get_size(self.base_path)
        self.start_time = time.time()

    def simple_post_ingestion_callback(self, column):
        delta_time = time.time() - self.start_time
        delta_size = get_size(self.base_path) - self.start_size

        log.info("Ingested single column %s",
                 column.id)
        log.info("Ingested %s MB in %s seconds, rate %s Mb/s",
                 delta_size / 1024 ** 2, delta_time, delta_size / 1024 ** 2 / delta_time)

    def get_directory_for_column_id(self, column_id, create=False):
        # type: (ColumnID) -> str
        """Determine the path containing the .npy files for a given column."""

        path = self.base_path
        path = os.path.join(path, path_escape(column_id.archive_id))
        path = os.path.join(path, path_escape(column_id.column_type))
        path = os.path.join(path, path_escape(column_id.column_name))
        path = os.path.join(path, path_escape(column_id.timestamp))

        if create and not os.path.exists(path):
            os.makedirs(path)

        return path

def path_escape(str):
    # type: (str) -> str
    """Escape any path separators in a string so it can be used as the name of a single folder."""

    # return str.replace(os.path.sep, "\\" + os.path.sep)
    return str


def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size
