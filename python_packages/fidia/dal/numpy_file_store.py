from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Iterable, Type, Any
import fidia

# Python Standard Library Imports
import os
import pickle

# Other Library Imports
import numpy as np
import pandas as pd

# FIDIA Imports
from fidia.column import ColumnID, FIDIAColumn, FIDIAArrayColumn

# Other modules within this package
from ._dal_internals import *

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

# __all__ = ['Archive', 'KnownArchives', 'ArchiveDefinition']



class NumpyFileStore(object):

    def __init__(self, base_path):

        if not os.path.isdir(base_path):
            raise FileNotFoundError(base_path + " does not exist.")

        self.base_path = base_path

    def __repr__(self):
        return "NumpyFileStore(base_path={})".format(self.base_path)

    def get_value(self, column, object_id):
        # type: (fidia.FIDIAColumn, str) -> Any

        log.debug("Entered Function")

        try:
            fidia_column_id = ColumnID.as_column_id(column.id)
        except KeyError:
            # Column ID is not a FIDIA column ID. This Access Layer can't respond.
            raise DALCantRespond("ColumnID %s is not a FIDIA standard ColumnID." % column.id)

        log.debug("hi")

        data_dir = self.get_directory_for_column_id(fidia_column_id)

        if not os.path.exists(data_dir):
            raise DALDataNotAvailalbe("NumpyFileStore has no data for ColumnID %s" % fidia_column_id)

        log.debug("hi")

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

        log.debug("hi")

        # Sanity checks that data loaded matches expectations
        # assert column.type ==

        assert data is not None

        log.debug("Returning data")

        return data

    def ingest_column(self, column):
        # type: (fidia.FIDIAColumn) -> None

        try:
            fidia_column_id = ColumnID.as_column_id(column.id)
        except KeyError:
            # Column ID is not a FIDIA column ID. This Access Layer can't respond.
            raise DALIngestionError("ColumnID %s is not a FIDIA standard ColumnID." % fidia_column_id)

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



    def ingest_archive(self, archive):
        # type: (fidia.Archive) -> None
        """Ingest all columns found in archive into this data access layer.

        Notes
        -----

        First pass implementation of this is "dumb": it just loops over all
        columns, ingesting them separately. In future, it would be better to
        look at the columns and group them intelligently e.g. by FITS file, so
        that we don't need to open every file many (hundreds) of times.

        """

        for column in archive.columns.values():
            self.ingest_column(column)



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
