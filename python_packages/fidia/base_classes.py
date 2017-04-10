"""This module provides all of the base classes used in FIDIA.



"""

from __future__ import absolute_import, division, print_function, unicode_literals


# Python Standard Library Imports

# Other Library Imports

# FIDIA Imports

# NOTE: This module should not import anything from FIDIA as that would
#       likely to cause a circular import error.

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


class BaseArchive(object):

    def writeable(self):
        raise NotImplementedError("")

    # @property
    # def contents(self):
    #     raise NotImplementedError("")

    def get_full_sample(self):
        raise NotImplementedError("")

    def get_trait(self, object_id=None, trait_key=None, parent_trait=None):
        raise NotImplementedError("")