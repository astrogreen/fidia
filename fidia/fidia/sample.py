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

import collections

from .astro_object import AstronomicalObject
from .archive import BaseArchive


class Sample(collections.MutableMapping):

    # ____________________________________________________________________
    # Sample Creation

    def __init__(self):

        # For now, all Samples are read only:
        self.read_only = True

        # Place to store the list of IDs contained in this sample
        self._ids = set()

        # Place to store the list of objects contained in this sample
        self._contents = dict()

        # Set of archives this object is attached to:
        self._archives = set()

        # The archive which recieves write requests
        self._write_archive = None

    @classmethod
    def new_from_archive(cls, archive):
        if not isinstance(archive, BaseArchive):
            raise Exception()


    # ____________________________________________________________________
    # Functions to create dictionary like behaviour

    def __getitem__(self, key):
        """Function called on dict type read access"""
        if key in self._ids:
            return self._contents[key]
        elif self.read_only:
            raise Exception("Object not found in sample.")
        else:
            # Create a new object and return it
            self.add_object(self._write_archive.default_object(identifier=key))
            return self._contents[key]

    def __setitem__(self, key, value):
        if self.read_only:
            raise Exception("Cannot assign to read-only sample")

    def __delitem__(self, key):
        if self.read_only:
            raise Exception()

    def keys(self):
        return self._ids

    def __len__(self):
        return len(self._ids)

    def __iter__(self):
        return self._ids


    @property
    def contents(self):
        return self._objects

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


        
