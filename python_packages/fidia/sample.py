"""
Samples are the primary interface to data in FIDIA.


Samples have a concept of what objects they contain (may or may not be all of
the objects offered by a particular archive.)

Samples know which archives contain data for a given object, and what kinds of
data are offered:

For exmaple, a survey might mantain a dictionary of properties as keys with
values as the corresponding archive which contains their values.

Samples also allow for tabular access to the data. Data filtering is achieved
by creating new (sub) sample. 

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import collections

import pandas as pd

from .astro_object import AstronomicalObject
from .archive.base_archive import BaseArchive

from .exceptions import *


class Sample(collections.MutableMapping):

    # ____________________________________________________________________
    # Sample Creation

    def __init__(self):

        # For now, all Samples are read only:
        self.read_only = True

        # Place to store ID crossmatches between archives
        self._id_cross_matches = None

        # Place to store the list of IDs contained in this sample
        #
        # Deprecated in favour of using Pandas and _id_cross_maches
        #self._ids = set()

        # Place to store the list of objects contained in this sample
        self._contents = dict()

        # Set of archives this object is attached to:
        self._archives = set()

        # The archive which recieves write requests
        self._write_archive = None

        # The mutable property defines whether objects can be added and
        # removed from this sample. The property latches on False.
        self._mutable = True

    @classmethod
    def new_from_archive(cls, archive):
        # @TODO: not complete!
        if not isinstance(archive, BaseArchive):
            raise Exception()

    # ____________________________________________________________________
    # Functions to create dictionary like behaviour

    def __getitem__(self, key):
        """Function called on dict type read access"""
        if key in self._contents.keys():
            # Then the requested object has been created. Nothing to do.
            return self._contents[key]
        elif key in self._id_cross_matches.index:
            # The request object exists in the archive, but has not been created for this sample.
            # TODO: Move the following line to it's own function and expand.
            self._contents[key] = AstronomicalObject(self, identifier=key)
            return self._contents[key]
        elif self.read_only:
            # The requested object is unknown, and we're not allowed to create a new one.
            raise NotInSample("Object '{}' not found in sample.".format(key))
        else:
            # Create a new object and return it
            self.add_object(self._write_archive.default_object(self, identifier=key))
            return self._contents[key]

    def __setitem__(self, key, value):
        if self.read_only:
            raise Exception("Cannot assign to read-only sample")

    def __delitem__(self, key):
        if self.read_only:
            raise Exception()

    def __len__(self):
        return len(self._id_cross_matches)

    def __iter__(self):
        return iter(self._id_cross_matches.index)

    # def get_archive_id(self, object, archive):
    #     pass

    def extend(self, id_list):
        if not isinstance(id_list, pd.DataFrame):
            # must convert input into a dataframe
            id_list = pd.DataFrame(index=Index(id_list).drop_duplicates())

        if self._id_cross_matches is None:
            self._id_cross_matches = id_list
        else:
            self._id_cross_matches.merge(id_list, 
                how='outer', left_index=True, right_index=True)

    def get_tabular_data(self):
        """
        Put this method just to follow the pattern. Nothing special happens here.
        :return:
        """

        return self._archives.tabular_data

    def tabular_data(self):
        """Return all tabular data as a single DataFrame."""

        # For each archive, get a DataFrame of data for objects indexed in
        # this sample.
        reordered_dataframes = []
        for ar in self._archives:
            # Reorder the data frame to match the sample index
            df = ar.tabular_data.reindex(index=self._id_cross_matches[ar.name])
            # Replace the index on the archive data with the sample index
            df.index = self._id_cross_matches.index
            reordered_dataframes.append(df)
        # Join the reordered archive data by (now the local sample) index
        return pd.concat(reordered_dataframes, axis=1)

    @property
    def ids(self):
        return self.keys()
    # @ids.setter
    # def ids(self, value):
    #     if self._mutable and not self.read_only:
    #         # @TODO: sanity checking of value!
    #         if self._id_cross_matches is None:
    #         self._ids = pd.Series(value)

    @property
    def mutable(self):
        return self._mutable
    @mutable.setter
    def mutable(self, value):
        if self._mutable and isinstance(value, bool):
            self._mutable = value



    # @property
    # def contents(self):
    #     return self._objects

    @property
    def archives(self):
        return self._archives

    def add_from_archive(self, archive):
        if not isinstance(archive, BaseArchive):
            raise Exception()
        if archive not in self._archives:
            self._archives.add(archive)
            if self._write_archive is None and archive.writeable():
                self.write_archive = archive
                self.read_only = False
    
    @property
    def write_archive(self):
        return self._write_archive
    @write_archive.setter
    def write_archive(self, value):
        if not isinstance(value, BaseArchive):
            raise Exception("That is not an archive.")
        if value in self._archives:
            self._write_archive = value
        else:
            raise Exception("Write archive must already be attached to the sample.")



    def add_object(self, value):
        if self.read_only:
            raise Exception("Sample is read only")
        self._write_archive.add_object(value)
        self._ids.add(value.identifier)
        self._contents[value.identifier] = value


    def available_data(self):
        # @TODO: No tests.
        available_data = {}
        for ar in self._archives:
            available_data[ar.name] = ar.available_data
        return available_data

    def get_archive_for_property(self, key):
        # TODO: this will return the first archive (in arbitrary order) that can answer the trait request.
        for ar in self.archives:
            if ar.can_provide(key):
                return ar
        # If no archive can provide the given trait_key, then raise an exception.
        raise UnknownTrait(key)

    def get_archive_id(self, archive, sample_id):
        # @TODO: Sanity checking, e.g. archive is actually valid, etc.

        return self._id_cross_matches.loc[sample_id][archive.name]

