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

from typing import Union, List, Tuple
import fidia

# Python Standard Library Imports

# Other Library Imports
import pandas as pd
import numpy as np

# FIDIA Imports
from .import base_classes as bases
from .column import ColumnID
from .exceptions import *

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


class Sample(bases.Sample):

    # ____________________________________________________________________
    # Sample Creation

    def __init__(self):

        from . import traits

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
        self._archives_by_id = dict() # type: Dict[str, fidia.Archive]
        self._primary_archive = None

        # The archive which receives write requests
        self._write_archive = None

        # Trait Mapping database for this sample
        self.trait_registry = traits.TraitMappingDatabase()

        # The mutable property defines whether objects can be added and
        # removed from this sample. The property latches on False.
        self._mutable = True

    @classmethod
    def new_from_archive(cls, archive):
        # type: (fidia.Archive) -> Sample
        if not isinstance(archive, bases.Archive):
            log.debug("Attempt to create new Sample from invalid archive object '%s'", archive)
            raise ValueError("Argument must be a FIDIA Archive.")
        sample = cls()

        sample._id_cross_matches = pd.DataFrame(pd.Series(archive.contents, name=archive.name, index=archive.contents))
        sample._archives = [archive]
        sample._archives_by_id[archive.archive_id] = archive
        sample.trait_registry.link_database(archive.trait_mappings)

        return sample
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


    def get_feature_catalog_data(self):
        """(Construct) A table of featured data from each archive in this sample."""

        first_row = True
        trait_properties = []  # type: List[Tuple[fidia.Trait, fidia.traits.TraitProperty]]
        trait_paths = []  # type: List[fidia.traits.TraitPath]

        for archive in self._archives:
            # TODO: This code won't support more than one archive!
            data_table = []
            for id in self:
                row = [id]
                for trait_property_path in archive.feature_catalog_data:
                    value = trait_property_path.get_trait_property_value_for_object(self[id])
                    if isinstance(value, (np.int64, np.int32)):
                        value = int(value)
                    row.append(value)
                    if first_row:
                        trait_properties.append(
                            (trait_property_path.get_trait_class_for_archive(archive),
                             trait_property_path.get_trait_property_for_archive(archive))
                        )
                        trait_paths.append(trait_property_path)
                data_table.append(row)
                first_row = False

        # Construct column names and units
        column_names = ["ID"]
        column_units = [""]
        for tp, path in zip(trait_properties, trait_paths):
            # Get the pretty name of the Trait
            qualifier = path[-1].trait_qualifier
            col_name = tp[0].get_pretty_name(qualifier)
            # Append the TraitProperty name only if it is not the default
            if tp[1].name is not 'value':
                col_name += " " + tp[1].get_pretty_name()
            # Append the Trait's branch name
            branch = path[-1].branch
            if branch:
                col_name += " (" + tp[0].branches_versions.get_pretty_name(branch) + ")"
            column_names.append(col_name)

            # Get the unit associated with the trait
            formatted_unit = tp[0].get_formatted_units()
            column_units.append(formatted_unit)

        return {'data': data_table,
                'column_names': column_names,
                'trait_paths': trait_paths,
                'units': column_units}


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

    def archive_for_column(self, id):
        """The `.Archive` instance that that has the column id given."""
        # type: (str) -> fidia.Archive
        # column_id = ColumnID.as_column_id(id)
        archive_id = id.split(":")[0]
        return self._archives_by_id[archive_id]

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
        # @TODO: Sanity checking, e.g. archive is actually valid, etc.

        return self._id_cross_matches.loc[sample_id][archive.name]

