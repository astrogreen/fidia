from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List

# Python Standard Library Imports
from collections import OrderedDict

# Other Library Imports
import pandas as pd

import sqlalchemy as sa
from sqlalchemy.orm import relationship
# from sqlalchemy.orm.collections import attribute_mapped_collection



# FIDIA Imports
import fidia.base_classes as bases
from ..utilities import SchemaDictionary, fidia_classname
# import fidia.sample as sample
import fidia.traits as traits
import fidia.column as columns
import fidia.cache as cache
# Other modules within this package
# from fidia.base_classes import BaseArchive

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['Archive']


class Archive(bases.Archive, bases.SQLAlchemyBase):
    """An archive of data."""
    column_definitions = columns.ColumnDefinitionList()

    # Set up how Archive objects will appear in the MappingDB
    __tablename__ = "archives"
    _db_id = sa.Column(sa.Integer, sa.Sequence('archive_seq'), primary_key=True)
    _db_calling_arguments = sa.Column(sa.String)
    _db_archive_class = sa.Column(sa.String)
    _trait_mappings = relationship(traits.TraitMapping)  # type: List[traits.TraitMapping]

    _id = None

    # This provides a space for an archive to set which catalog data to
    # "feature". These properties are those that would be displayed e.g. when
    # someone wants an overview of the data in the archive, or for a particular
    # object.
    feature_catalog_data = []  # type: List[traits.TraitPath]


    def __init__(self):

        # Copy input trait_mappings list to the database for persistence.
        assert isinstance(self.trait_mappings, list)
        self._trait_mappings = self.trait_mappings
        self._mapping_db = None  # type: traits.TraitManager

        self._db_archive_class = fidia_classname(self)

        super(Archive, self).__init__()

        # Associate column instances with this archive instance
        local_columns = columns.ColumnDefinitionList()
        for alias, column in self.column_definitions:
            log.debug("Associating column %s with archive %s", column, self)
            instance_column = column.associate(self)
            local_columns.add((alias, instance_column))
        self.columns = local_columns

    @property
    def trait_manager(self):
        # type: () -> traits.TraitManager
        if self._mapping_db is None:
            log.debug("Received first request for Mapping DB on Archive %s", self)
            self._mapping_db = traits.TraitManager()
            assert isinstance(self._mapping_db, traits.TraitManager)
            self._mapping_db.register_mapping_list(self._trait_mappings)
        return self._mapping_db

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, value):
        self._contents = set(value)

    @property
    def archive_id(self):
        if self._id is None:
            return repr(self)
        return self._id

    def get_full_sample(self):
        """Return a sample containing all objects in the archive."""
        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        from fidia.sample import Sample
        new_sample = Sample()
        id_cross_match = pd.DataFrame(pd.Series(map(str, self.contents), name=self.name, index=self.contents))

        # For a new, empty sample, extend effectively just copies the id_cross_match into the sample's ID list.
        new_sample.extend(id_cross_match)

        # Add this archive to the set of archives associated with the sample.
        new_sample._archives = {self}
        new_sample._primary_archive = self

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        return new_sample


    def type_for_trait_path(self, path):
        """Return the type for the provided Trait path.

        :param path:
            A sequence object containing the pieces of the "path" addressing the
            object of interest.

        This function is a shortcut to determine what kind of object one should
        expect if requesting a particular Trait or trait property as defined by
        the path provided. This is a shortcut, i.e., the Traits are not actually
        constructed. It shouldn't be considered absolutely authoritative, but
        should be close.

        Currently, this can only differentiate between a Trait and a Trait Property.
        This could be made more specific in one of several ways:

        - Have the schema include type information when it is constructed.
        - Find the appropriate class by querying the TraitMapping object
          at each level.

        """

        # Drill down the schema:
        schema = self.schema(by_trait_name=True)
        current_schema_item = schema
        for path_element in path:
            trait_key = traits.TraitKey.as_traitkey(path_element)
            current_schema_item = current_schema_item[trait_key.trait_name]

        # Decide whether the item in the schema corresponds to a Trait or TraitProperty
        if isinstance(current_schema_item, dict):
            return traits.Trait
        else:
            return traits.TraitProperty

    def can_provide(self, trait_key):
        trait_key = traits.TraitKey.as_traitkey(trait_key)
        return trait_key.trait_name in self.available_traits.get_trait_names()



class BasePathArchive(Archive):
    def __init__(self, **kwargs):
        self.basepath = kwargs.pop('basepath')
        super(BasePathArchive, self).__init__(**kwargs)


class KnownArchives(dict):

    __instance = None

    def __new__(cls, *args, **kwargs):
        if KnownArchives.__instance is None:
            KnownArchives.__instance = dict.__new__(cls)
        return KnownArchives.__instance



