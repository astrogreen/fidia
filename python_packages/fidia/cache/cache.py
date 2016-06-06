"""
The FIDIA Caching System


"""

from abc import ABCMeta, abstractproperty, abstractclassmethod, abstractmethod

from ..exceptions import DataNotAvailable, ReadOnly
from ..traits import Trait

from collections import OrderedDict

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

class Cache(metaclass=ABCMeta):

    read_only = True

    def __init__(self, loading='verylazy'):
        """

        :param archive:
        :param loading:
        :return:
        """

        if loading not in ('lazy', 'verylazy'):
            raise ValueError("Caching must be one of 'lazy' or 'verylazy'")

        self.backing_cache = None

    @abstractmethod
    def get_cached_trait_property(self, object_id, trait_key_path, trait, trait_property_name):
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
    def check_trait_property_available(self, object_id, trait_key_path, trait_property_name):
        """Check if the cache is likely to contain data for the requested TraitProperty.

        Ideally, this function should return as quickly as possible, therefore, it
        is *not* required to guarantee that the data is actually available.
        (`get_cached_trait_property` will raise an exception if necessary.)

        If simply retrieving the data will be just as fast, then this should just return True.

        :param trait_key_path: Sequence containing the Trait keys of each level in
        the hierarchy leading to the requested data.
        :param trait_property_name: (string) Name of the requested TraitProperty.
        :return: True or False

        """
        raise NotImplementedError

    def get_cached_trait(self, object_id, trait_key_path, trait_class):
        """Load a whole Trait from the cache.

        The default implementation simply calls `get_cached_trait_property` for
        each trait property. This function should be overridden where the cache can
        optimise requests for the whole Trait.

        """

        trait_property_names = trait_class.trait_property_dir()

        trait_property_dict = dict()
        for trait_property_name in trait_property_names:
            try:
                trait_property_dict[trait_property_name] = self.get_cached_trait_property(
                    object_id, trait_key_path, trait_property_name)
            except KeyError:
                log.debug("Property %s of trait %s is not in the cache.",
                          trait_property_name, trait_key_path)
        return trait_property_dict

    def update_cached_trait_property(self, object_id, trait_key_path, trait_property_name, value):
        """Update the cached data corresponding to the provided TraitProperty.

        If the cache is read-only, this should raise a FIDIA ReadOnly exception.

        :param trait_key_path: Tuple containing the Trait keys of each level in
        the hierarchy leading to the requested data.

        :param trait_property_name: (string) Name of the requested TraitProperty.
        :return:

        """
        raise ReadOnly

    def update_cached_trait(self, object_id, trait_key_path, trait_dict):
        """Update the cached data for the given Trait.

        If the cache is read-only, this should raise a FIDIA ReadOnly exception.

        :param trait_key_path: Tuple containing the Trait keys of each level in
        the hierarchy leading to the requested data.

        :param trait_property_name: (string) Name of the requested TraitProperty.
        :param trait_dict: (dict-like) Dictionary of trait properties for this trait.
        :return: None.

        """

        for trait_property_name in trait_dict:
            self.update_cached_trait_property(trait_key_path, trait_property_name, trait_dict[trait_property_name])

    def clear_trait_property_data(self, trait_key_path, trait_property_name):
        raise NotImplementedError

    def cache_request(self, trait, trait_property_name):
        """Serve a cache request, or pass it on to the backing cache.

        If this cache can serve the request, then it does.

        If not, then the request is forwarded to the next cache, and the return
        value is attempted to be added to this cache before returning the value.
        """

        assert isinstance(trait, Trait)

        # Local variable to store the retrieved value.
        result = None

        trait_path = trait.trait_path

        # Check if this cache can respond to the request:
        if self.check_trait_property_available(trait.object_id, trait_path, trait_property_name):
            try:
                result = self.get_cached_trait_property(trait.object_id, trait_path, trait_property_name)
            except DataNotAvailable:
                pass
            except:
                log.exception("Uncaught cache error.")

        if result is None:
            # This cache could not answer the request, raise to next level.

            if self.backing_cache is None:
                # No higher caches. Return request to calling trait.
                result = getattr(trait, trait_property_name).uncached_value
            else:
                result = self.backing_cache.cache_request(trait, trait_property_name)

        assert result is not None, "Programming error."

        if self.read_only is False:
            # Add the result to this cache
            self.update_cached_trait_property(trait.object_id, trait_path, trait_property_name, result)

        return result


class MemoryCache(Cache):

    def __init__(self, **kwargs):
        self._cache = OrderedDict()
        self.read_only = False
        super(MemoryCache, self).__init__(**kwargs)

    # def update_cached_trait(self, object_id, trait_key_path, trait_dict):
    #     self._cache[(object_id, trait_key_path)] = trait_dict

    def update_cached_trait_property(self, object_id, trait_key_path, trait_property_name, value):
        if (object_id, trait_key_path) not in self._cache:
            self._cache[(object_id, trait_key_path)] = dict()
        self._cache[(object_id, trait_key_path)][trait_property_name] = value

    def get_cached_trait_property(self, object_id, trait_key_path, trait, trait_property_name):
        return self._cache[(object_id, trait_key_path)][trait_property_name]

    # def get_cached_trait(self, object_id, trait_key_path, trait_class):
    #     return self._cache[(object_id, trait_key_path)]

    def check_trait_property_available(self, object_id, trait_key_path, trait_property_name):
        return (object_id, trait_key_path) in self._cache
