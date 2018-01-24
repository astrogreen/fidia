from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Any, Dict
import fidia

# Python Standard Library Imports
import inspect
from itertools import chain

# Other Library Imports
# import numpy as np
import pandas as pd

# FIDIA Imports
from fidia.column import FIDIAArrayColumn
from fidia.exceptions import DataNotAvailable

# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['DataAccessLayer',
           'DataAccessLayerHost',
           'OptimizedIngestionMixin',
           'DALException', 'DALCantRespond', 'DALDataNotAvailable', 'DALIngestionError']

class DALException(Exception):
    """Generic exception class for the Data Access Layer."""

class DALCantRespond(DALException):
    """Exception raised when a layer of the DAL doesn't know about the column/data requested."""

class DALDataNotAvailable(DALException):
    """Exception raised when a layer of the DAL doesn't have the requested data."""

class DALIngestionError(DALException):
    """Exception raised when an error occurs loading new data into a layer of the DAL."""


class DataAccessLayer(object):
    """Base class for implementing layers of the FIDIA Data Access System.

    This class should be subclassed for creating new data access layers. As
    and absolute minimum, subclasses must implement the `.get_value` method.

    To support data ingestion, subclasses must implement `.ingest_column`.
    Optimization via the `OptimizedIngestionMixin` is highly recommended, but
    requires subclasses to implement additional methods.


    Subclasses can implement the following callback functions to be notified of particular stages of ingestion:

    - `simple_pre_ingestion_callback(column)`
    - `simple_post_ingestion_callback(column)`


    See Also
    --------

    :class:`fidia.dal.NumpyFileStore`: an example of a working subclass of this base
        class.

    :class:`fidia.dal.OptimizedIngestionMixin`: override mixin providing optimized
        data ingestion.

    """

    def __repr__(self):

        # Attempt to work out the arguments for the DAL initialization:
        sig = inspect.signature(self.__init__)

        arg_list = []

        for arg in sig.parameters.keys():
            arg_list.append(arg)
            try:
                arg_list.append("=" + str(getattr(self, arg)))
            except:
                pass

        return self.__class__.__name__ + "(" + ", ".join(arg_list) + ")"


    def get_value(self, column, object_id):
        """(Abstract) Return data for the specified column and object_id.

        This method must be overridden in subclasses of :class:`DataAccessLayer`.

        This method may raise the following special exceptions:

        * :class:`DALCantRespond`
        * :class:`DALDataNotAvailable`

        """
        raise NotImplementedError()

    def ingest_column(self, column):
        """(Abstract) Add the data available from the specified column to this layer.

        Layers implementing this method will be able to ingest data.

        """
        raise NotImplementedError()

    def ingest_archive(self, archive):
        # type: (fidia.Archive) -> None
        """Ingest all columns found in archive into this data access layer.

        This implementation of full archive ingestion is "dumb": it just loops
        over all columns, ingesting them separately. Strongly consider using the
        `OptimizedIngestionMixin` which provides a smarter ingestion that takes
        advantage of column grouping.

        """

        if isinstance(self, OptimizedIngestionMixin):
            raise Exception("Programming error: OptimizedIngestionMixin must be listed "
                            "before DataAccessLayer in definition of class %s" % self.__class__.__name__)

        for column in archive.columns.values():

            if hasattr(self, 'simple_pre_ingestion_callback'):
                self.simple_pre_ingestion_callback(column)

            self.ingest_column(column)

            if hasattr(self, 'simple_post_ingestion_callback'):
                self.simple_post_ingestion_callback(column)

class OptimizedIngestionMixin:
    """An override mixin that provides optimized data ingestion for subclasses of `DataAccessLayer`.

    Warnings
    --------

    This class must be listed before `DataAccessLayer` in the base classes of
    any subclasses, otherwise the optimized ingestion won't be used.

    """

    def ingest_object_with_data(self, column, object_id, data):
        # type: (fidia.FIDIAColumn, str, Any) -> None
        """(Abstract) Optimised ingestion of a the given data for a particular object in a column.

        Implementation of this method in subclasses is not required.

        """
        raise NotImplementedError()

    def ingest_column_with_data(self, column, data):
        # type: (fidia.FIDIAColumn, Any) -> None
        """(Abstract) Optimised ingestion of a the given data for a whole column.

        Implementation of this method in subclasses is not required.

        """
        raise NotImplementedError()

    def ingest_column(self, column):
        """(Abstract) Add the data available from the specified column to this layer.

        Layers implementing this method will be able to ingest data.

        """
        raise NotImplementedError()

    def ingest_archive(self, archive):
        # type: (fidia.Archive) -> None
        """Ingest all columns found in archive into this data access layer with column grouping optimization.

        Subclasses can implement the following callback functions to be notified of particular stages of ingestion:

        - `simple_pre_ingestion_callback(column)`
        - `simple_post_ingestion_callback(column)`
        - `by_object_group_pre_ingestion_callback(object_id, grouping_context)`
        - `by_object_group_post_ingestion_callback(object_id, grouping_context)`
        - `by_column_group_pre_ingestion_callback(grouping_context)`
        - `by_column_group_post_ingestion_callback(grouping_context)`

        """

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

        # Remove the columns that can be grouped from the list of unsorted columns:
        for column in chain.from_iterable(grouped_columns.values()):
            unsorted_columns.remove(column)


        # Ingest each group of columns
        for grouping_context, column_group in grouped_columns.items():

            a_column = column_group[0]
            a_column_definition = a_column.column_definition_class.from_id(a_column.id.column_name)

            # Column groups are such that the `prepare_context` function of any
            # column in the group can be used to create the context for any other
            # column in the group.

            group_context_manager = a_column_definition.prepare_context

            # Reconstruct the arguments that must be passed to the getters
            # (similar to what is done in `ColumnDefinition.associate`)
            sig = inspect.signature(group_context_manager)
            arguments = {archive_attr: getattr(archive, archive_attr)
                         for archive_attr in sig.parameters.keys()
                         if archive_attr != "object_id"}

            # Decide if this column_group should be accessed by object (using object_getter) or as a whole:
            if hasattr(a_column_definition, 'object_getter_from_context'):

                #  __          __   __        ___  __  ___     __   __   __        __
                # |__) \ /    /  \ |__)    | |__  /  `  |     / _` |__) /  \ |  | |__)
                # |__)  |     \__/ |__) \__/ |___ \__,  |     \__> |  \ \__/ \__/ |
                #
                # This group of columns is optimised to have all of the columns
                # values retrieved object by object (in some sense "row
                # ordered"). This is probably a situation where there is a file per object.
                #
                # Below, the outer loop is over objects, with a context manager
                # being created for each object, and then data for individual
                # columns are read for that object.
                #
                # Array-valued data is ingested immediately using
                # `ingest_object_with_data`. Single-valued data is held in
                # memory until all objects have been processed, and then
                # ingested using `ingest_column_with_data`.
                #
                # All requests for data are carefully wrapped to catch
                # exceptions expected from data not being present, and skip
                # those data while logging the skip.

                non_array_column_data = dict()

                for object_id in archive.contents:

                    if hasattr(self, 'by_object_group_pre_ingestion_callback'):
                        self.by_object_group_pre_ingestion_callback(object_id, grouping_context)

                    # @TODO: This set of try-except blocks is getting a bit ridiculous. Surely we could do better?
                    try:
                        with group_context_manager(object_id, **arguments) as context:
                            for column in column_group:
                                coldef = column.column_definition_class.from_id(column.id.column_name)
                                try:
                                    data = coldef.object_getter_from_context(object_id, context, **arguments)
                                except Exception as e:
                                    log.warning("No data ingested for object '%s' in column '%s' due to exception %s: %s",
                                                object_id, column.id, e.__class__.__name__, str(e))
                                    if log.isEnabledFor(slogging.DEBUG):
                                        log.exception("Exception Traceback")
                                    pass
                                else:
                                    if isinstance(column, FIDIAArrayColumn):
                                        self.ingest_object_with_data(column, object_id, data)
                                    else:
                                        if column not in non_array_column_data:
                                            non_array_column_data[column] = pd.Series(index=archive.contents,
                                                                                      dtype=type(data))
                                        non_array_column_data[column][object_id] = data
                    except DataNotAvailable:
                        continue

                    if hasattr(self, 'by_object_group_post_ingestion_callback'):
                        self.by_object_group_post_ingestion_callback(object_id, grouping_context)

                for column, data in non_array_column_data.items():
                    self.ingest_column_with_data(column, data)


            elif hasattr(a_column_definition, 'array_getter_from_context'):

                #  __          __   __                           __   __   __        __
                # |__) \ /    /  ` /  \ |    |  |  |\/| |\ |    / _` |__) /  \ |  | |__)
                # |__)  |     \__, \__/ |___ \__/  |  | | \|    \__> |  \ \__/ \__/ |
                #
                # This group of columns is optimised to have all of the columns
                # values retrieved in one go for multiple columns (in some sense
                # "column ordered"). For example, there might be one file
                # containing many whole columns.
                #
                # Below, a context manager is created for the whole group, and
                # then individual columns data are retrieved in the inner loop.

                with group_context_manager(**arguments) as context:

                    if hasattr(self, 'by_column_group_pre_ingestion_callback'):
                        self.by_column_group_pre_ingestion_callback(grouping_context)

                    for column in column_group:
                        coldef = column.column_definition_class.from_id(column.id.column_name)
                        data = coldef.array_getter_from_context(context, **arguments)
                        self.ingest_column_with_data(column, data)

                    if hasattr(self, 'by_column_group_post_ingestion_callback'):
                        self.by_column_group_post_ingestion_callback(grouping_context)

            else:
                raise Exception("Programming error: grouped column must have either `object_getter_from_context` "
                                "or `array_getter_from_context`")


        # Fall back to dumb ingestion for any remaining columns.
        for column in unsorted_columns:

            if hasattr(self, 'simple_pre_ingestion_callback'):
                self.simple_pre_ingestion_callback(column)

            self.ingest_column(column)

            if hasattr(self, 'simple_post_ingestion_callback'):
                self.simple_post_ingestion_callback(column)



class DataAccessLayerHost(object):
    """Hosts a set of data access layers.

    Typically, a FIDIA/Python process will have only one instance of this class,
    `fidia.dal_host`. The contents of the host are initialized from the
    :mod:`configparser.ConfigParser` instance provided to the constructor.
    Layers of an existing host can be changed by modifying :attr:`.layers`
    directly.

    """

    def __init__(self, config):
        """Create a DAL host with all DAL layers described in fidia.ini file as provided by `config`."""

        if hasattr(self, 'layers'):
            # Already initialised
            return

        self.layers = []  # type: List[fidia.dal.NumpyFileStore]

        for section in config:

            # Skip sections of the config file not related to the Data Access Layer
            if not section.startswith("DAL-"):
                log.debug("Skipping non-DAL configuration section %s", section)
                continue

            new_layer_class_name = section[4:]

            if new_layer_class_name in __all__:
                log.error("FIDIA Configuration Error: DAL Layer type %s is invalid", new_layer_class_name)
                continue

            log.debug("Trying to create DAL Layer for class '%s'", new_layer_class_name)
            try:
                new_layer_class = getattr(fidia.dal, new_layer_class_name)
            except:
                log.error("FIDIA Configuration Error: DAL Layer type %s is unknown", new_layer_class_name)
                raise
            new_layer = new_layer_class(**config[section])

            self.layers.append(new_layer)

    def __repr__(self):
        result = "Data Access Layer Host with layers:\n"

        for index, dal_layer in enumerate(self.layers):
            result += "    {index}: {layer}\n".format(index=index, layer=repr(dal_layer))

        return result

    def search_for_cell(self, column, object_id):
        # type: (fidia.FIDIAColumn, str) -> Any
        """Iterate through the DAL looking for a layer that provides the requested data."""

        log.debug("Searching DAL for data for col: %s, obj: %s", column, object_id)

        for dal_layer in self.layers:
            log.debug("Trying layer %s", dal_layer)
            try:
                data = dal_layer.get_value(column, object_id)
            except DALCantRespond as e:
                log.info(e, exc_info=True)
            except DALDataNotAvailable as e:
                log.info(e, exc_info=True)
            except:
                raise DALException("Unexpected error in data retrieval")
            else:
                return data

        # All layers have been exhausted. The DAL has no data for the request.
        raise DALDataNotAvailable()
