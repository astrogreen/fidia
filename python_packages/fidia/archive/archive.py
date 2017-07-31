from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Iterable, Type
import fidia

# Python Standard Library Imports
from collections import OrderedDict, Mapping
from copy import deepcopy

# Other Library Imports
import pandas as pd

import sqlalchemy as sa
from sqlalchemy.sql import and_, or_, not_
from sqlalchemy.orm import relationship, reconstructor, object_session
from sqlalchemy.orm.collections import attribute_mapped_collection



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


class Archive(bases.Archive, bases.SQLAlchemyBase, bases.PersistenceBase):
    """An archive of data in FIDIA.

    Instances of `.Archive` class are created by calling the constructor for an
    `.ArchiveDefinition`, which defines the objects, data, and schema of the
    Archive. `.Archive` and it's sub-classes are generic across all specific
    Archives in the system.

    An `.ArchiveDefinition` can define Traits and TraitCollections, which are
    checked and registered when the corresponding archive is created. As part of
    the registration, each TraitMapping is validated. This validation checks
    each Trait's slots have been correctly filled (e.g. with another trait or a
    column of a particular type).

    An `.Archive` also behaves like a `.Sample` in that its objects can be
    looked up looked up by subscripting. So these two are equivalent:

    >>> ea = fidia.ExampleArchive(basepath=test_data_dir)
    >>> sample = fidia.Sample.new_from_archive(ea)
    >>> mass = sample['Gal1'].dmu['StellarMasses'].table['StellarMasses'].stellar_mass

    and

    >>> ea = fidia.ExampleArchive(basepath=test_data_dir)
    >>> mass = ea['Gal1'].dmu['StellarMasses'].table['StellarMasses'].stellar_mass

    """

    # Set up how Archive objects will appear in the MappingDB
    __tablename__ = "archives"
    _db_id = sa.Column(sa.Integer, sa.Sequence('archive_seq'), primary_key=True)
    _db_archive_class = sa.Column(sa.String)
    _db_archive_id = sa.Column(sa.String)
    _db_calling_arguments = sa.Column(sa.PickleType)
    # _db_contents = sa.Column(sa.PickleType)
    __mapper_args__ = {
        'polymorphic_on': '_db_archive_class',
        'polymorphic_identity': 'Archive'}

    _mappings = relationship('TraitMapping')  # type: List[traits.TraitMapping]
    columns = relationship('FIDIAColumn',
                           collection_class=attribute_mapped_collection('id')
                           )  # type: Dict[str, columns.FIDIAColumn]

    # This provides a space for an archive to set which catalog data to
    # "feature". These properties are those that would be displayed e.g. when
    # someone wants an overview of the data in the archive, or for a particular
    # object.
    feature_catalog_data = []  # type: List[traits.TraitPath]


    def __init__(self, **kwargs):
        """Pass through initializer. Initialization is handled by `ArchiveDefinition.__new__()`

        Warnings:

            This should be empty, or nearly so. It will be called when an
            Archive is reconstructed from the database (which is non-standard
            behavior for SQLAlchemy). See `Archive.__db_init__`

        """
        super(Archive, self).__init__()


    @reconstructor
    def __db_init__(self):
        """Initializer called when the object is reconstructed from the database."""
        super(Archive, self).__db_init__()
        # Since this archive is being recovered from the database, it must have
        # requested persistence.
        # self._db_session = Session()
        self._local_trait_mappings = None

        # Call initialisers of subclasses so they can reset attributes stored in _db_calling_args
        self.__init__(**self._db_calling_arguments)

    def register_mapping(self, mapping):
        # type: (traits.TraitMapping) -> None
        """Register a new TraitMapping to this Archive."""
        self._register_mapping_locally(mapping)
        self._mappings.append(mapping)

    def _register_mapping_locally(self, mapping):
        """Add a TraitMapping to the `_local_trait_mappings`."""
        if isinstance(mapping, traits.TraitMapping):
            mapping.validate()
            key = mapping.mapping_key
            log.debug("Registering mapping for key %s", key)
            # Check if key already exists in this database
            if key in self._local_trait_mappings:
                raise FIDIAException("Attempt to add/change an existing mapping")
            self._local_trait_mappings[key] = mapping
            # @TODO: Also link up superclasses of the provided Trait to the FIDIA level.
        else:
            raise ValueError("TraitManager can only register a TraitMapping, got %s"
                             % mapping)

    @property
    def contents(self):
        # type: () -> List[str]
        from ..astro_object import AstronomicalObject

        # Get a valid database session:
        #
        #   I'm not sure if the object_session is required, but it guarantees
        #   that we are working with the session that this archive belongs to.
        #   In theory, fidia.mappingdb_session should be the only session present.
        session = object_session(self)
        if session is None:
            session = fidia.mappingdb_session

        query = session.query(AstronomicalObject._identifier)

        query_results = query.filter_by(_db_archive_id=self._db_archive_id).all()
        # Results will contain a list of tuples, so we must get the first column out so we have a simple list.

        contents = [i[0] for i in query_results]  # type: List[str]
        return contents

    @contents.setter
    def contents(self, value):
        # type: (Iterable) -> None
        from ..astro_object import AstronomicalObject

        # Get a valid database session:
        #
        #   I'm not sure if the object_session is required, but it guarantees
        #   that we are working with the session that this archive belongs to.
        #   In theory, fidia.mappingdb_session should be the only session present.
        session = object_session(self)
        if session is None:
            session = fidia.mappingdb_session

        # Work out what's changed
        new_contents = set(value)
        existing_contents = set(self.contents)
        to_add = new_contents.difference(existing_contents)
        to_remove = existing_contents.difference(new_contents)

        # Make those changes to the underlying Objects table in the database
        object_table = AstronomicalObject.__table__
        if len(to_add) > 0:
            session.execute(object_table.insert(),
                            [{"_identifier": i, "_db_archive_id": self._db_archive_id} for i in to_add])
        if len(to_remove) > 0:
            session.execute(object_table.delete().where(and_(object_table.c._db_archive_id == self._db_archive_id,
                                                             object_table.c._identifier in to_remove)))


    @property
    def archive_id(self):
        return self._db_archive_id

    @property
    def trait_mappings(self):
        # type: () -> Dict[Tuple[str, str], fidia.traits.TraitMapping]
        if self._local_trait_mappings is None:
            # Have not been initialised
            self._local_trait_mappings = MultiDexDict(2)
            for mapping in self._mappings:
                self._register_mapping_locally(mapping)
        return self._local_trait_mappings



    def get_archive_id(self, archive, id):
        # Part of the "sample-like interface
        if archive is not self:
            raise FIDIAException("Object in Archive cannot get id's for other archives.")
        else:
            return id

    def archive_for_column(self, column_id):
        # Part of the "sample-like interface
        column_id = fidia.column.ColumnID.as_column_id(column_id)
        log.debug("Column requested: %s", column_id)
        if column_id.archive_id != self.archive_id:
            log.error("Archive ID mismatch for column %s. This archive: %s, column: %s",
                      column_id, self.archive_id, column_id.archive_id)
            raise FIDIAException("Object in Archive cannot get columns from other archives.")
        return self

    def find_column(self, column_id):
        # Part of the "sample-like interface
        column_id = fidia.column.ColumnID.as_column_id(column_id)
        return self.columns[column_id]

    def get_full_sample(self):
        """Return a sample containing all objects in the archive."""
        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        from fidia.sample import Sample
        new_sample = Sample()
        id_cross_match = pd.DataFrame(pd.Series(map(str, self.contents), name=self.archive_id, index=self.contents))

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


    def __getitem__(self, key):
        # type: (str) -> AstronomicalObject
        """Make archives able to retrieve their astro-objects in the same manner as samples."""
        # Part of the "sample-like interface

        from ..astro_object import AstronomicalObject

        if key in self.contents:
            return AstronomicalObject(self, identifier=key)
        else:
            raise NotInSample("Archive '%s' does not contain object '%s'" % (self, key))


class BasePathArchive(Archive):

    __mapper_args__ = {'polymorphic_identity': 'BasePathArchive'}

    def __init__(self, **kwargs):
        """Initializer.

        Note: Normally, this initialiser would not be called when reconstructing
        form the database, but for Archives, it is. See `Archive.__db_init__`.

        """

        self.basepath = kwargs['basepath']
        super(BasePathArchive, self).__init__(**kwargs)


class DatabaseArchive(Archive):

    __mapper_args__ = {'polymorphic_identity': 'DatabaseArchive'}

    def __init__(self, **kwargs):
        """Initializer.

        Note: Normally, this initialiser would not be called when reconstructing
        form the database, but for Archives, it is. See `Archive.__db_init__`.

        """

        self.database_url = kwargs['database_url']
        super(DatabaseArchive, self).__init__(**kwargs)

def replace_aliases_trait_mappings(mappings, alias_mappings):
    for mapping in mappings:
        if isinstance(mapping, fidia.traits.TraitPropertyMapping):
            if mapping.id in alias_mappings:
                log.debug("Replacing alias %s with actual ID %s", mapping.id, alias_mappings[mapping.id])
                mapping.id = alias_mappings[mapping.id]
            else:
                continue
        else:
            log.debug("Recursing on mapping %s", mapping)
            replace_aliases_trait_mappings(mapping, alias_mappings)

class ArchiveDefinition(object):
    """A definition of the columns (data), objects, and traits (schema) making up an archive.

    This class should be subclassed to define a new Archive for use in FIDIA.
    Typically, the subclass needs to define the following attributes:

    `.archive_id`: The ID uniquely identifying this archive. Typically, this
    will be composed of the Survey/Archive name. If individual instances of the
    archive may need to refer to different data (e.g., because it is stored in
    different directories, then the ID should contain this distinction in the
    form of a path or similar. If the data to be referred to is always the same
    (more typical) then the ID should not contain the path.

    `.archive_type`: The class of the `.Archive` to be constructed.
    `.BasePathArchive` is the most common example, which provides a base path
    abstraction to remove details of the particular local path from the rest of
    the definition of the archive.

    `.contents`: An iterable containing the names of the objects to be included
    in this Archive. May be instance specific (but only if the `.archive_id` is
    also instance specific).

    `.column_definitions`: List of definitions of the columns of data to be
    included in this archive. When the `.ArchiveDefinition` factory creates an
    instances of an `.Archive`, these definitions will be interpreted into
    actual references to columns of data.

    `.trait_mappings`: List of TraitMapping objects defining the schemas of the
    data in this archive.

    `.is_persisted`: bool which determines if FIDIA is allowed to write Archive
    instances from this definition into the MappingDB. Typically only set to
    False for testing.

    """


    archive_id = None

    archive_type = Archive  # type: Type[Archive]
    writable = False

    contents = []  # type: Iterable

    trait_mappings = []  # type: List[traits.TraitMapping]
    column_definitions = dict()  # type: Dict[str, columns.ColumnDefinition]

    is_persisted = True

    def __init__(self, **kwargs):
        # __init__ of superclasses not called.
        pass

    # noinspection PyProtectedMember
    def __new__(cls, **kwargs):

        from fidia import known_archives

        definition = object.__new__(cls)
        definition.__init__(**kwargs)

        # Allow an archive not to (individually) be persisted in the database
        is_persisted = kwargs.pop("persist", True) and definition.is_persisted

        # @TODO: Validate definition

        if is_persisted:
            # Check if archive already exists:
            try:
                return known_archives.by_id[definition.archive_id]
            except KeyError:
                pass

        # Archive doesn't exist, so it must be created
        archive = definition.archive_type.__new__(definition.archive_type)

        # I n i t i a l i s e   t h e   A r  c h i v e
        archive.__init__(**kwargs)

        # We wrap the rest of the initialisation in a database transaction, so
        # if the archive cannot be initialised, it will not appear in the
        # database.
        with database_transaction(fidia.mappingdb_session):

            # Basics
            archive._db_archive_id = definition.archive_id
            archive.writeable = definition.writable
            archive.contents = definition.contents
            archive._db_calling_arguments = kwargs

            # TraitMappings

            #     Note: To ensure that this instance of the archive has local copies
            #     of all of the Trait Mappings and Column definitions, we make
            #     copies of the originals. This is necessary so that e.g. if they
            #     are defined on a class instead of an instance, the copies
            #     belonging to an instance are unique. Without this, SQLAlchemy will
            #     complain that individual TraitMappings are owned by multiple
            #     archives.

            archive._local_trait_mappings = MultiDexDict(2)  # type: Dict[Tuple[str, str], traits.TraitMapping]
            archive._mappings = deepcopy(definition.trait_mappings)
            for mapping in archive._mappings:
                archive._register_mapping_locally(mapping)

            archive._db_archive_class = fidia_classname(archive)

            # Columns
            column_definitions = deepcopy(definition.column_definitions)  # type: List[Tuple[str, columns.ColumnDefinition]]

            # Associate column instances with this archive instance
            alias_mappings = dict()
            for alias, column in column_definitions:
                log.debug("Associating column %s with archive %s", column, archive)
                instance_column = column.associate(archive)
                archive.columns[instance_column.id] = instance_column
                alias_mappings[alias] = instance_column.id

            # Update any columns that have been referred to by an alias:
            replace_aliases_trait_mappings(archive._mappings, alias_mappings)

            # self._db_session.add(self.trait_manager)
            if is_persisted:
                fidia.mappingdb_session.add(archive)

        return archive

class KnownArchives(object):

    _instance = None

    @property
    def _query(self):
        # type: () -> sa.orm.query.Query
        return fidia.mappingdb_session.query(Archive)

    # The following __new__ function implements a Singleton.
    def __new__(cls, *args, **kwargs):
        if KnownArchives._instance is None:
            instance = object.__new__(cls)

            KnownArchives._instance = instance
        return KnownArchives._instance

    @property
    def all(self):
        # type: () -> List[Archive]
        return self._query.order_by('_db_archive_id').all()


    class by_id(object):
        def __getitem__(self, item):
            # type: (str) -> Archive
            log.debug("Retrieving archive with id \"%s\"...", item)
            log.debug("Query object: %s", KnownArchives()._query)
            try:
                archive = KnownArchives()._query.filter_by(_db_archive_id=item).one()
            except:
                log.warn("Request for unknown archive %s.", item)
                raise KeyError("No archive with id '%s'" % item)
            else:
                log.debug("...archive %s found.", item)
                return archive
    by_id = by_id()

