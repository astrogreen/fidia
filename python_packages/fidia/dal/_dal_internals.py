from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Iterable, Type, Any
import fidia

# Python Standard Library Imports

# Other Library Imports
import numpy as np

# FIDIA Imports
# from fidia.local_config import config
# from fidia.column import ColumnID

# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['DALException', 'DALCantRespond', 'DALDataNotAvailalbe', 'DALIngestionError']

class DALException(Exception): pass

class DALCantRespond(DALException): pass

class DALDataNotAvailalbe(DALException): pass

class DALIngestionError(DALException): pass

class DataAccessLayerHost(object):

    _instance = None

    # # The following __new__ function implements a Singleton.
    # def __new__(cls, *args, **kwargs):
    #     if DataAccessLayerHost._instance is None:
    #         instance = object.__new__(cls)
    #
    #         DataAccessLayerHost._instance = instance
    #     return DataAccessLayerHost._instance

    def __init__(self, config):
        """Create a DAL host with all DAL layers described in fidia.ini file."""

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
                log.info(e.message, exc_info=True)
                pass
            except DALDataNotAvailalbe as e:
                log.info(e.message, exc_info=True)
                pass
            except:
                raise DALException("Unexpected error in data retrieval")
            else:
                return data

        # All layers have been exhausted. The DAL has no data for the request.
        raise DALDataNotAvailalbe()
