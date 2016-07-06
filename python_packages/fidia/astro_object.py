
import collections

from .traits.utilities import TraitKey, parse_trait_key

class AstronomicalObject(collections.MutableMapping):

    def __init__(self, sample, identifier=None, ra=None, dec=None):
        if identifier is None:
            if ra is None or dec is None:
                raise Exception("Either 'identifier' or 'ra' and 'dec' must be defined.")
            self._identifier = "J{ra:3.6}{dec:+2.4d}".format(ra=ra, dec=dec)
        else:
            self._identifier = identifier

        # Reference to the sample containing this object.
        self.sample = sample

        # Dictionary of IDs for this object in the various archives attached
        # to the sample. @TODO: Initialised to None: must be populated
        # seperately.
        self._archive_id = {archive: None for archive in sample.archives}

        self._ra = ra
        self._dec = dec
        super(AstronomicalObject, self).__init__()

    @property
    def identifier(self):
        return self._identifier

    @property
    def ra(self):
        return self._ra

    @property
    def dec(self):
        return self._dec


    # ____________________________________________________________________
    # Functions to create dictionary like behaviour to address Traits of the galaxy
    #
    #     These are required as part of the collections.MutableMapping class.

    def __getitem__(self, key):
        """Function called on dict type read access"""

        if isinstance(key, list):
            # We have been asked for more than one property, will return tabular data?
            # @TODO!
            raise Exception("List indexing behaviour not implemented.")
        else:
            key = parse_trait_key(key)
            #raise Exception("Key indexing behaviour not implemented.")
            # # Asked for a single property
            # archive = self.sample.get_archive_for_property(key)
            # archive.data.loc[self._archive_id[archive]][key]

            archive = self.sample.get_archive_for_property(key)

            archive_id = self.sample.get_archive_id(archive, self.identifier)
            # get_trait provides a reference to a cached copy of the trait held by the archive.
            # It may be necessary to actually save a reference in this object when it comes to
            # object storage.
            return archive.get_trait(archive_id, key)

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def keys(self):
        """Provide a list of (presumed) valid TraitKeys for this object"""
        keys = set()
        for ar in self.sample.archives:
            keys.update(ar.available_traits.get_all_traitkeys())


        return keys

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())



