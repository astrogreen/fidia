"""This module provides all of the base classes used in FIDIA.



"""

from __future__ import absolute_import, division, print_function, unicode_literals


# Python Standard Library Imports
from abc import ABCMeta, abstractclassmethod, abstractproperty

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


class AbstractBaseTrait(metaclass=ABCMeta):

    @abstractclassmethod
    def schema(cls):
        raise NotImplementedError

    # @abstractproperty
    def value(self):
        raise NotImplementedError

    # @abstractproperty
    # def description(self): raise NotImplementedError

    # @abstractproperty
    # def data_type(self): raise NotImplementedError

    # @abstractproperty
    # def reference(self): raise NotImplementedError


class AbstractNumericTrait(AbstractBaseTrait):

    @abstractproperty
    def unit(self):
        raise NotImplementedError


class AbstractBaseArrayTrait(AbstractBaseTrait):

    @abstractproperty
    def shape(self):
        raise NotImplementedError


class AbstractMeasurement(AbstractNumericTrait):

    # @abstractproperty
    # def epoch(self):
    #     raise NotImplementedError
    # @abstractproperty
    # def instrument(self):
    #     raise NotImplementedError

    pass


class AbstractBaseClassification(AbstractBaseTrait):

    @abstractproperty
    def valid_classifications(self):
        raise NotImplementedError