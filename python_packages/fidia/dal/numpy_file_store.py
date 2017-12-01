from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Any
import fidia

# Python Standard Library Imports
import os
import pickle

# Other Library Imports
import numpy as np
import pandas as pd

# FIDIA Imports
from fidia.column import ColumnID, FIDIAArrayColumn

# Other modules within this package
from ._dal_internals import *

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
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

        try:
            fidia_column_id = ColumnID.as_column_id(column.id)
        except KeyError:
            # Column ID is not a FIDIA column ID. This Access Layer can't respond.
            raise DALCantRespond("ColumnID %s is not a FIDIA standard ColumnID." % column.id)

        data_dir = self.get_directory_for_column_id(fidia_column_id)

        if not os.path.exists(data_dir):
            raise DALDataNotAvailable("NumpyFileStore has no data for ColumnID %s" % fidia_column_id)

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

        try:
            fidia_column_id = ColumnID.as_column_id(column.id)
        except KeyError:
            # Column ID is not a FIDIA column ID. This Access Layer can't respond.
            raise DALIngestionError("ColumnID %s is not a FIDIA standard ColumnID." % column.id)

        data_dir = self.get_directory_for_column_id(fidia_column_id)

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        if isinstance(column, FIDIAArrayColumn):
            # Data is in array format, and therefore each cell is stored as a separate file.
            for object_id in column.contents:
                data = column.get_value(object_id, provenance='definition')
                data_path = os.path.join(data_dir, object_id + ".npy")
                np.save(data_path, data, allow_pickle=False)
        else:
            # Data is individual values, so is stored in a single pickled pandas series

            data_path = os.path.join(data_dir, "pandas_series.pkl")

            data = column.get_array()
            log.debug(type(data))
            series = pd.Series(data, index=column.contents)
            series.to_pickle(data_path)

    def get_directory_for_column_id(self, column_id):
        # type: (ColumnID) -> str
        """Determine the path containing the .npy files for a given column."""


        path = self.base_path
        path = os.path.join(path, path_escape(column_id.archive_id))
        path = os.path.join(path, path_escape(column_id.column_type))
        path = os.path.join(path, path_escape(column_id.column_name))
        path = os.path.join(path, path_escape(column_id.timestamp))

        return path

def path_escape(str):
    # type: (str) -> str
    """Escape any path separators in a string so it can be used as the name of a single folder."""

    # return str.replace(os.path.sep, "\\" + os.path.sep)
    return str
