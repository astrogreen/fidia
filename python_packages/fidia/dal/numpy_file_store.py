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

        data_dir = self.get_directory_for_column_id(fidia_column_id, True)

        if isinstance(column, FIDIAArrayColumn):
            # Data is in array format, and therefore each cell is stored as a separate file.
            for object_id in column.contents:
                try:
                    data = column.get_value(object_id, provenance='definition')
                except:
                    log.warning("No data ingested for object '%s' in column '%s'", object_id, column.id)
                    pass
                else:
                    data_path = os.path.join(data_dir, object_id + ".npy")
                    np.save(data_path, data, allow_pickle=False)
        else:
            # Data is individual values, so is stored in a single pickled pandas series

            data_path = os.path.join(data_dir, "pandas_series.pkl")

            data = column.get_array()
            log.debug(type(data))
            series = pd.Series(data, index=column.contents)
            series.to_pickle(data_path)

    def ingest_object_with_data(self, column, object_id, data):
        # type: (fidia.FIDIAColumn, str, Any) -> None

        try:
            fidia_column_id = ColumnID.as_column_id(column.id)
        except KeyError:
            # Column ID is not a FIDIA column ID. This Access Layer can't respond.
            raise DALIngestionError("ColumnID %s is not a FIDIA standard ColumnID." % column.id)

        data_dir = self.get_directory_for_column_id(fidia_column_id, True)

        if isinstance(column, FIDIAArrayColumn):
            # Data is in array format, and therefore each cell is stored as a separate file.
            data_path = os.path.join(data_dir, object_id + ".npy")
            np.save(data_path, data, allow_pickle=False)
        else:
            raise DALIngestionError("NumpyFileStore.ingest_object_with_data() works only for array data.")

    def ingest_column_with_data(self, column, data):

        try:
            fidia_column_id = ColumnID.as_column_id(column.id)
        except KeyError:
            # Column ID is not a FIDIA column ID. This Access Layer can't respond.
            raise DALIngestionError("ColumnID %s is not a FIDIA standard ColumnID." % column.id)

        data_dir = self.get_directory_for_column_id(fidia_column_id, True)

        if isinstance(column, FIDIAArrayColumn):
            # Array column
            pass
        else:
            data_path = os.path.join(data_dir, "pandas_series.pkl")
            if isinstance(data, pd.Series):
                series = data
            else:
                series = pd.Series(data, index=column.contents)
            series.to_pickle(data_path)

    def ingest_archive(self, archive):

        def get_size(start_path='.'):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(start_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size


        # Create a local list of columns, from which we can remove columns that
        # have a smarter way of being ingested.
        unsorted_columns = list(archive.columns.values())

        # Go through the columns available, and collect together
        # columns that share the same `grouping_context`

        grouped_columns = dict()  # type: Dict[str, List[fidia.FIDIAColumn]]
        for column in unsorted_columns:
            # Reconstruct the ColumnDefinition object that would create this column.
            coldef = column.column_definition_class.from_id(column.id.column_name)

            if hasattr(coldef, 'grouping_context'):
                if coldef.grouping_context not in grouped_columns:
                    grouped_columns[coldef.grouping_context] = []
                grouped_columns[coldef.grouping_context].append(column)

        for column in chain.from_iterable(grouped_columns.values()):
            unsorted_columns.remove(column)

        for column_group in grouped_columns.values():

            a_column = column_group[0]
            a_column_definition = a_column.column_definition_class.from_id(a_column.id.column_name)

            # Column groups are such that the `prepare_context` function of any
            # column in the group can be used to create the context for any other
            # column in the group.

            group_context_manager = a_column_definition.prepare_context

            # Reconstruct the arguments that must be passed to the getters
            # (similar to what is done in `ColumnDefinition.associate`)
            sig = inspect.signature(group_context_manager)
            # arguments = dict()
            # for archive_attr in sig.parameters.keys():
            #     if archive_attr == 'object_id':
            #         # Don't process the object_id parameter as an archive attribute.
            #         continue
            #     arguments[archive_attr] = getattr(archive, archive_attr)

            arguments = {archive_attr: getattr(archive, archive_attr)
                         for archive_attr in sig.parameters.keys()
                         if archive_attr != "object_id"}

            # Decide if this column_group should be accessed by object or not:
            if hasattr(a_column_definition, 'object_getter_from_context'):

                non_array_column_data = dict()

                for object_id in archive.contents:
                    start_size = get_size(self.base_path)
                    start_time = time.time()

                    # @TODO: This set of try-except blocks is getting a bit ridiculous. Surely we could do better?
                    try:
                        with group_context_manager(object_id, **arguments) as context:
                            for column in column_group:
                                coldef = column.column_definition_class.from_id(column.id.column_name)
                                if isinstance(column, FIDIAArrayColumn):
                                    try:
                                        data = coldef.object_getter_from_context(object_id, context, **arguments)
                                    except:
                                        log.warning("No data ingested for object '%s' in column '%s'",
                                                    object_id, column.id)
                                        pass
                                    else:
                                        self.ingest_object_with_data(column, object_id, data)
                                else:
                                    try:
                                        data = coldef.object_getter_from_context(object_id, context, **arguments)
                                    except:
                                        log.warning("No data ingested for object '%s' in column '%s'",
                                                    object_id, column.id)
                                        pass
                                    else:
                                        if column not in non_array_column_data:
                                            non_array_column_data[column] = pd.Series(index=archive.contents,
                                                                                      dtype=type(data))
                                        non_array_column_data[column][object_id] = data
                    except DataNotAvailable:
                        continue


                    delta_time = time.time() - start_time
                    delta_size = get_size(self.base_path) - start_size

                    log.info("Ingested Grouped columns %s for object %s",
                             a_column_definition.grouping_context, object_id)
                    log.info("Ingested %s MB in %s seconds, rate %s Mb/s",
                             delta_size / 1024 ** 2, delta_time, delta_size / 1024 ** 2 / delta_time)

                for column, data in non_array_column_data.items():
                    self.ingest_column_with_data(column, data)


            elif hasattr(a_column_definition, 'array_getter_from_context'):
                with group_context_manager(object_id, **arguments) as context:
                    for column in column_group:
                        coldef = column.column_definition_class.from_id(column.id.column_name)
                        data = coldef.array_getter_from_context(context, **arguments)
                        self.ingest_column_with_data(column, data)

            else:
                raise Exception("Programming error: grouped column must have either `object_getter_from_context` "
                                "or `array_getter_from_context`")


        # Fall back to dumb ingestion for any remaining columns.
        for column in unsorted_columns:
            start_size = get_size(self.base_path)
            start_time = time.time()
            self.ingest_column(column)
            delta_time = time.time() - start_time
            delta_size = get_size(self.base_path) - start_size

            log.info("Ingested Column %s",
                     column.id)
            log.info("Ingested %s MB in %s seconds, rate %s Mb/s",
                     delta_size/1024**2, delta_time, delta_size/1024**2/delta_time)


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
