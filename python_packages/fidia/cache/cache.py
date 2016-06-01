"""
The FIDIA Caching System


"""

from abc import ABCMeta, abstractproperty, abstractclassmethod, abstractmethod

from ..exceptions import DataNotAvailable, ReadOnly

class Cache(metaclass=ABCMeta):

    read_only = True

    def __init__(self, archive=None, loading='verylazy'):
        """

        :param archive:
        :param loading:
        :return:
        """

        if loading not in ('lazy', 'verylazy'):
            raise ValueError("Caching must be one of 'lazy' or 'verylazy'")

    @abstractmethod
    def get_cached_trait_property(self, object_id, trait_key_path, trait_property_name):
        """Retrieve the data corresponding to the provided TraitProperty.

        If the data is not available, this should raise the DataNotAvailable exception.

        Implementation Details

            The trait_key_path provided will be a sequence (i.e. a tuple or list) of
            TraitKey objects. The order of the sequence corresponds to the hierarchy
            of the requested data, with the most general/higest level trait first, and
            sub-traits after that.

        :param object_id: The id of the requested object. This should match the ID scheme
        for the corresponding archive to which the cache is attached.

        :param trait_key_path: Tuple containing the Trait keys of each level in
        the hierarchy leading to the requested data.

        :param trait_property_name: (string) Name of the requested TraitProperty.
        :return:

        """
        raise NotImplementedError

    @abstractmethod
    def check_trait_property_available(self, trait_key_path, trait_property_name):
        """Check if the cache is likely to contain data for the requested TraitProperty.

        Ideally, this function should return as quickly as possible, therefore, it
        is *not* required to guarantee that the data is actually available.
        (`get_cached_trait_property` will raise an exception if necessary.)

        :param trait_key_path: Sequence containing the Trait keys of each level in
        the hierarchy leading to the requested data.
        :param trait_property_name: (string) Name of the requested TraitProperty.
        :return: True or False

        """
        raise NotImplementedError

    def update_cached_trait_property(self, trait_key_path, trait_property_name):
        """Update the cached data corresponding to the provided TraitProperty.

        If the cache is read-only, this should raise a FIDIA ReadOnly exception.

        :param trait_key_path: Tuple containing the Trait keys of each level in
        the hierarchy leading to the requested data.

        :param trait_property_name: (string) Name of the requested TraitProperty.
        :return:

        """
        raise ReadOnly

    def clear_trait_property_data(self, trait_key_path, trait_property_name):
        raise NotImplementedError
