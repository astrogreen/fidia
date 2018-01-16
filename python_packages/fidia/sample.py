"""
Samples are the primary interface to data in FIDIA.


Samples have a concept of what objects they contain (may or may not be all of
the objects offered by a particular archive.)

Samples know which archives contain data for a given object, and what kinds of
data are offered:

For example, a survey might maintain a dictionary of properties as keys with
values as the corresponding archive which contains their values.

Samples also allow for tabular access to the data. Data filtering is achieved
by creating new (sub) sample. 

"""
from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Union, List, Tuple, Dict
import fidia

# Python Standard Library Imports

# Other Library Imports
import pandas as pd
import numpy as np
from cached_property import cached_property

# FIDIA Imports
from .import base_classes as bases
from .exceptions import *
from .utilities import MultiDexDict, reset_cached_property, MappingMixin

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


__all__ = ['Sample']

class Sample(bases.Sample, MappingMixin):
    """Samples in FIDIA are typically the result of a query.

    Samples provide two main functions: define a specific list of objects
    included (which need not be all of the objects from any one archive); and
    provide cross matching functionality between different archives.

    Samples have access to all of the data available in the archives that they
    are connected with.

    """
    # ____________________________________________________________________
    # Sample Creation

    def __init__(self):

        # Until there is something in the sample, it is useless.
        self.is_populated = False

        # For now, all Samples are read only:
        self.read_only = True

        # Place to store ID cross matches between archives
        self._id_cross_matches = None

        # Place to store the list of objects contained in this sample
        self._contents = dict()

        # List of archives included in this Sample
        self._archives = []  # type: List[fidia.Archive]
        self._primary_archive = None

        # The archive which receives write requests
        self._write_archive = None

        # Trait Mapping database for this sample
        # self.trait_registry = traits.TraitManager()

        # The mutable property defines whether objects can be added and
        # removed from this sample. The property latches on False.
        self._mutable = True

        # Place to store a list of TraitPointers currently present on this Sample.
        self._trait_pointers = set()

    @classmethod
    def new_from_archive(cls, archive):
        # type: (fidia.Archive) -> Sample
        if not isinstance(archive, bases.Archive):
            log.debug("Attempt to create new Sample from invalid archive object '%s'", archive)
            raise ValueError("Argument must be a FIDIA Archive.")
        sample = cls()

        sample._id_cross_matches = pd.DataFrame(
            pd.Series(archive.contents, name=archive.archive_id, index=archive.contents))
        sample.link_archive(archive)

        return sample


    def link_archive(self, archive, index=-1):
        # type: (fidia.Archive, int) -> None
        assert isinstance(archive, fidia.Archive)
        self._archives.insert(index, archive)

        # Reset the corresponding cached_property if necessary.
        reset_cached_property(self, '_archives_by_id')
        reset_cached_property(self, 'trait_mappings')
        self._update_trait_pointers()


    @cached_property
    def trait_mappings(self):
        # type: () -> MultiDexDict
        result = MultiDexDict(2)
        for archive in self._archives:
            # @TODO: Check that this is actually going through the archives in the right order!
            result.update(archive.trait_mappings)
        return result

    def _update_trait_pointers(self):

        if not hasattr(self, '_trait_pointers'):
            self._trait_pointers = set()
            # This second check of initialization is necessary if the object has been restored from the database.

        from fidia.traits.trait_utilities import TraitPointer

        # Clear all existing pointers to TraitPointers
        while self._trait_pointers:
            # Set of tratit_pointers is not empty
            attr_name  = self._trait_pointers.pop()
            attr = getattr(self, attr_name)
            assert isinstance(attr, bases.TraitPointer)
            delattr(self, attr_name)

        log.debug("Creating Trait Pointers for Archive %s", self)
        if log.isEnabledFor(slogging.VDEBUG):
            message = str(self.trait_mappings.as_nested_dict())
            log.vdebug("TraitMappings available: %s", message)
        for trait_type in self.trait_mappings.keys(1):
            # pointer_name = snake_case(trait_mapping.trait_class.trait_class_name())
            log.debug("Adding TraitPointer '%s'", trait_type)
            self._trait_pointers.add(trait_type)
            setattr(self, trait_type, TraitPointer(trait_type, self, None, self.trait_mappings))

    # ____________________________________________________________________
    # Functions to create dictionary like behaviour

    def __getitem__(self, key):
        # type: (Union[str, bases.TraitKey]) -> AstronomicalObject
        """Function called on dict type read access"""

        from .astro_object import AstronomicalObject

        if key in self._contents.keys():
            # Then the requested object has been created. Nothing to do.
            return self._contents[key]
        elif key in self._id_cross_matches.index:
            # The request object exists in the archive, but has not been created for this sample.
            # # TODO: Move the following line to it's own function and expand.
            # # Check if the primary archive has catalog_coordinates, and if so get the RA and DEC
            # coord_key = traits.TraitKey("catalog_coordinate")
            # if self._primary_archive.can_provide(coord_key):
            #     coord = self._primary_archive.get_trait(key, coord_key)
            #     ra = coord._ra()
            #     dec = coord._dec()
            # else:
            #     ra = None
            #     dec = None
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
            id_list = pd.DataFrame(index=pd.Index(id_list).drop_duplicates())

        if self._id_cross_matches is None:
            self._id_cross_matches = id_list
        else:
            self._id_cross_matches.merge(id_list, 
                how='outer', left_index=True, right_index=True)



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
    def contents(self):
        """This makes Sample and Archive both have the same accessor for a list of data object ids."""
        # @TODO: This should probably be refactored. Archive and Sample need to work the same way here.
        return list(self.ids)

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

    @cached_property
    def _archives_by_id(self):
        # type: () -> Dict[str, fidia.Archive]
        return {a.archive_id: a for a in self._archives}

    def add_archive(self, archive):
        if not isinstance(archive, bases.Archive):
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
        if not isinstance(value, bases.Archive):
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

    def archive_for_column(self, column_id):
        # type: (str) -> fidia.Archive
        """The `.Archive` instance that that has the column id given."""
        # Part of the sample-like interface.
        #
        # NOTE: changes to the logic here may also need to be made in `Sample.archive_for_column`

        column_id = fidia.column.ColumnID.as_column_id(column_id)
        log.debug("Column requested: %s", column_id)
        column_type = column_id.type  # Cache locally to avoid recalculating.
        if column_type != 'full':
            # This column is not fully defined in the FIDIA sense. Either:
            #    (1) there was an error or problem in associating the column with
            #        this archive--check the execution of `replace_aliases_trait_mappings`
            #        and `expand_column_ids_in_trait_mappings` in `ArchiveDefinition.__new__`
            #    (2) the column id string does not conform to the FIDIA standard, presumably
            #        because the data access layer recognises a special column id. In this
            #        case we assume that the column is associated with the Archive providing
            #        the mapping, but we cannot know which Archive that is here. Perhaps it
            #        would be possible to raise an exception that could make this clear to
            #        the calling function.
            if column_type == 'non-conformant':
                # @TODO: Handle non-conformant ColumnIDs: see case (2) above.
                # Case (2) above.
                raise FIDIAException("Column %s has a non-standard ID and the associated Archive cannot be determined" %
                                     column_id)
            else:
                # Case (1) above.
                raise FIDIAException("Column %s does not seem to have been correctly associated with any archive" %
                                     column_id)
        archive_id = column_id.archive_id

        try:
            return self._archives_by_id[archive_id]
        except KeyError:
            raise FIDIAException("No archive is available in this Sample for column %s" % column_id)


    def find_column(self, column_id):
        """Look up the `.FIDIAColumn` instance for the provided ID."""
        # type: (str) -> fidia.FIDIAColumn
        # column_id = ColumnID.as_column_id(id)
        archive_id = column_id.split(":")[0]
        archive = self._archives_by_id[archive_id]
        columns = archive.columns  # type: fidia.column.ColumnDefinitionList
        col = columns[column_id]
        assert isinstance(col, fidia.FIDIAColumn)
        return col

    def get_archive_id(self, archive, sample_id):
        # type: (fidia.Archive, str) -> str
        # @TODO: Sanity checking, e.g. archive is actually valid, etc.

        return self._id_cross_matches.loc[sample_id][archive.archive_id]

