from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List
import fidia

# Python Standard Library Imports
from collections import OrderedDict, Mapping
from copy import deepcopy

# Other Library Imports
import pandas as pd

import sqlalchemy as sa
from sqlalchemy.orm import relationship, reconstructor
# from sqlalchemy.orm.collections import attribute_mapped_collection



# FIDIA Imports
import fidia.base_classes as bases
from ..exceptions import *
from ..utilities import SchemaDictionary, fidia_classname, MultiDexDict
from ..database_tools import database_transaction
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

__all__ = ['Archive', 'KnownArchives', 'ArchiveDefinition']


class Archive(bases.Archive, bases.SQLAlchemyBase):
    """An archive of data.

    An `.Archive` can define Traits and TraitCollections, which are checked and
    registered when the archive is created. As part of the registration, each
    TraitMapping is validated. This validation checks each Trait's slots have
    been correctly filled (e.g. with another trait or a column of a particular
    type).


    """
    column_definitions = columns.ColumnDefinitionList()

    # Set up how Archive objects will appear in the MappingDB
    __tablename__ = "archives"
    _db_id = sa.Column(sa.Integer, sa.Sequence('archive_seq'), primary_key=True)
    _db_archive_class = sa.Column(sa.String)
    _db_calling_arguments = sa.Column(sa.String)
    __mapper_args__ = {'polymorphic_on': "_db_archive_class"}

    _mappings = relationship('TraitMapping')  # type: List[TraitMapping]

    _id = None

    # This provides a space for an archive to set which catalog data to
    # "feature". These properties are those that would be displayed e.g. when
    # someone wants an overview of the data in the archive, or for a particular
    # object.
    feature_catalog_data = []  # type: List[traits.TraitPath]


    def __init__(self, **kwargs):

        self._local_trait_mappings = MultiDexDict(2)  # type: Dict[Tuple[str, str], TraitMapping]


        # Create a database session which will be used to handle transactions
        # associated with this archive.
        #  @TODO: Do this only if the archive is to be persisted.
        if kwargs.pop('persist', False):
            pass

        self._db_calling_arguments = repr(kwargs)

        with database_transaction(fidia.mappingdb_session):
            # We wrap the rest of the initialisation in a database transaction, so
            # if the archive cannot be initialised, it will not appear in the
            # database.

            assert isinstance(self.trait_mappings, list)
            # self.trait_manager = traits.TraitManager(session=self._db_session)
            # self.trait_manager.register_mapping_list(self.trait_mappings)

            for mapping in self.trait_mappings:
                self.register_mapping(mapping)



            self._db_archive_class = fidia_classname(self)

            super(Archive, self).__init__()

            # Associate column instances with this archive instance
            local_columns = columns.ColumnDefinitionList()
            for alias, column in self.column_definitions:
                log.debug("Associating column %s with archive %s", column, self)
                instance_column = column.associate(self)
                local_columns.add((alias, instance_column))
            self.columns = local_columns

            # self._db_session.add(self.trait_manager)
            fidia.mappingdb_session.add(self)

    @reconstructor
    def __db_init__(self):
        """Initializer called when the object is reconstructed from the database."""
        # Since this archive is being recovered from the database, it must have
        # requested persistence.
        # self._db_session = Session()
        pass

    def register_mapping(self, mapping):
        # type: (TraitMapping) -> None

        from fidia.traits import TraitMapping

        if isinstance(mapping, TraitMapping):
            mapping.validate()
            key = mapping.key()
            log.debug("Registering mapping for key %s", key)
            # Check if key already exists in this database
            if key in self._local_trait_mappings:
                raise FIDIAException("Attempt to add/change an existing mapping")
            self._local_trait_mappings[key] = mapping
            # @TODO: Also link up superclasses of the provided Trait to the FIDIA level.
        else:
            raise ValueError("TraitManager can only register a TraitMapping, got %s"
                             % mapping)


        self._mappings.append(mapping)

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
        self.basepath = kwargs['basepath']
        super(BasePathArchive, self).__init__(**kwargs)

class ArchiveDefinition(object):

    name = None
    archive_id = None

    archive_type = Archive
    writable = False

    def __init__(self, **kwargs):
        # __init__ of superclasses not called.
        pass

    def __new__(cls, **kwargs):

        from fidia import known_archives

        definition = object.__new__(cls)
        definition.__init__(**kwargs)

        # @TODO: Validate definition

        # Check if archive already exists:
        try:
            return known_archives.by_id[definition.archive_id]
        except KeyError:
            pass

        # Archive doesn't exist, so it must be created
        archive = definition.archive_type.__new__(definition.archive_type)

        # I n i t i a l i s e   t h e   A r  c h i v e

        # Basics
        archive._id = definition.archive_id
        archive.name = definition.name
        archive.writeable = definition.writable
        # archive._db_calling_arguments = repr(kwargs)
        archive._contents = definition._contents

        # TraitMappings
        archive.trait_mappings = deepcopy(definition.trait_mappings)
        archive.column_definitions = deepcopy(definition.column_definitions)
        #     Ensure that this instance of the archive has local copies of all
        #     of the Trait Mappings and Column definitions. This is necessary so
        #     that e.g. if they are defined on a class instead of an instance,
        #     the copies belonging to an instance are unique. Without this,
        #     SQLAlchemy will complain that individual TraitMappings are owned
        #     by multiple archives.

        archive.__init__(**kwargs)

        return archive

class KnownArchives(object):

    __instance = None

    # The following __new__ function implements a Singleton.
    def __new__(cls, *args, **kwargs):
        if KnownArchives.__instance is None:
            instance = object.__new__(cls)

            instance._query = fidia.mappingdb_session.query(Archive)  # type: sa.orm.query.Query

            KnownArchives.__instance = instance
        return KnownArchives.__instance

    @property
    def all(self):
        # type: () -> List[Archive]
        return self._query.order_by('archive_id').all()


    class by_id(object):
        def __getitem__(self, item):
            try:
                return KnownArchives.__instance._query.filter_by(archive_id=item).one()
            except:
                raise KeyError("No archive with id '%s'" % item)
    by_id = by_id()

