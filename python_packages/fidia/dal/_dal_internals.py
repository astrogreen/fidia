from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Any
import fidia

# Python Standard Library Imports
import inspect

# Other Library Imports
# import numpy as np

# FIDIA Imports

# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['DataAccessLayer',
           'DataAccessLayerHost',
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

    See Also
    --------

    :class:`fidia.dal.NumpyFileStore`: an example of a working subclass of this base
        class.

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

        Notes
        -----

        First pass implementation of this is "dumb": it just loops over all
        columns, ingesting them separately. In future, it would be better to
        look at the columns and group them intelligently e.g. by FITS file, so
        that we don't need to open every file many (hundreds) of times.

        """

        for column in archive.columns.values():
            self.ingest_column(column)



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
