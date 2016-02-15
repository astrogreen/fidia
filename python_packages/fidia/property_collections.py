class MagnitudeCollection(collections.MutableMapping):
    """A Sample of AstronomicalObjects.


    This is a subclass of collections.MutableMapping, which basically makes it
    behaive like a custom dictionary.

    """


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

