from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Iterable, Type, Any
import fidia

# Python Standard Library Imports
# from collections import OrderedDict, Mapping
from copy import deepcopy

# Other Library Imports
# import pandas as pd

import sqlalchemy as sa
from sqlalchemy.sql import and_
from sqlalchemy.orm import relationship, reconstructor, object_session
from sqlalchemy.orm.collections import attribute_mapped_collection

# FIDIA Imports
import fidia.base_classes as bases
from ..exceptions import *
from ..utilities import fidia_classname, MultiDexDict, MappingMixin
from ..database_tools import database_transaction
from fidia.sample import SampleLikeMixin
import fidia.traits as traits
import fidia.column as fidia_column
# Other modules within this package
# from fidia.base_classes import BaseArchive

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['Archive', 'KnownArchives', 'ArchiveDefinition']


class Archive(SampleLikeMixin, MappingMixin, bases.Archive, bases.Sample, bases.SQLAlchemyBase, bases.PersistenceBase):
    # noinspection PyUnresolvedReferences
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

        >>> ea = fidia.archive.example_archive.ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive
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
    _db_calling_arguments = sa.Column(sa.PickleType)  # type: Dict[str, Any]
    # _db_contents = sa.Column(sa.PickleType)
    __mapper_args__ = {
        'polymorphic_on': '_db_archive_class',
        'polymorphic_identity': 'Archive'}

    _mappings = relationship('TraitMapping',
                             cascade="all, delete, delete-orphan"
                             )  # type: List[traits.TraitMapping]
    columns = relationship('FIDIAColumn',
                           collection_class=attribute_mapped_collection('id'),
                           cascade="all, delete, delete-orphan"
                           )  # type: Dict[str, fidia_column.FIDIAColumn]

    def __init__(self, **kwargs):
        """Pass through initializer. Initialization is handled by `ArchiveDefinition.__new__()`

        Warnings:

            This should be empty, or nearly so. It will be called when an
            Archive is reconstructed from the database (which is non-standard
            behavior for SQLAlchemy). See `Archive.__db_init__`

        """
        self._local_trait_mappings = None
        super(Archive, self).__init__()


    @reconstructor
    def __db_init__(self):
        """Initializer called when the object is reconstructed from the database."""
        super(Archive, self).__db_init__()
        # Since this archive is being recovered from the database, it must have
        # requested persistence.
        # self._db_session = Session()
        self._local_trait_mappings = None

        # Call initializers of subclasses so they can reset attributes stored in _db_calling_args
        self.__init__(**self._db_calling_arguments)

    def register_mapping(self, mapping):
        # type: (traits.TraitMapping) -> None
        """Register a new TraitMapping to this Archive."""
        self._register_mapping_locally(mapping)
        self._mappings.append(mapping)
        self._update_trait_pointers()

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
        """Data Objects contained in this archive.

        Warnings
        --------

        The order of these objects is not preserved currently, because of how
        the data are stored in the persistence database. This may be valuable in
        future. In the short term, efforts have been made to make sure
        everything is checked and ensured to be done in the order of the
        contents for each instance, regardless of the original ordering.

        """
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
            # Have not been initialized

            # Confirm that the database has loaded its data, and if not, skip initialization.
            if len(self._mappings) == 0:
                return dict()

            # Otherwise, initialize the trait_mappings from the mappings stored int he database.
            self._local_trait_mappings = MultiDexDict(2)  # type: Dict[Tuple[str, str], fidia.traits.TraitMapping]
            for mapping in self._mappings:
                self._register_mapping_locally(mapping)
            self._update_trait_pointers()
        return self._local_trait_mappings



    def get_archive_id(self, archive, id):
        # Part of the "sample-like interface
        if archive is not self:
            raise FIDIAException("Object in Archive cannot get id's for other archives.")
        else:
            return id

    def archive_for_column(self, column_id):
        # type: (str) -> fidia.Archive
        """The `.Archive` instance that that has the column id given.

        This is part of the sample-like interface for Archives.

        See Also
        --------

        `Sample.archive_for_column`

        """
        
        # NOTE: changes to the logic here may also need to be made in `Sample.archive_for_column`

        column_id = fidia_column.ColumnID.as_column_id(column_id)
        log.debug("Column requested: %s", column_id)
        column_type = column_id.type  # Cache locally to avoid recalculating.
        if column_type != 'full':
            # This column is not fully defined in the FIDIA sense. Either:
            #    (1) there was an error or problem in associating the column with
            #        this archive--check the execution of `replace_aliases_trait_mappings`
            #        and `expand_column_ids_in_trait_mappings` in `ArchiveDefinition.__new__`
            #    (2) the column id string does not conform to the FIDIA standard, presumably
            #        because the data access layer recognises a special column id. In this
            #        we assume that the column is associated with this Archive (what else
            #        can we do?).
            if column_type == 'non-conformant':
                # Case (2) above.
                return self
            else:
                # Case (1) above.
                raise FIDIAException("Column %s does not seem to have been correctly associated with any archive" %
                                     column_id)
        if column_id.archive_id != self.archive_id:
            log.error("Archive ID mismatch for column %s. This archive: %s, column: %s",
                      column_id, self.archive_id, column_id.archive_id)
            raise FIDIAException("Object in Archive cannot get columns from other archives.")
        return self

    def find_column(self, column_id):
        # Part of the "sample-like interface
        column_id = fidia.column.ColumnID.as_column_id(column_id)
        return self.columns[column_id]

    def validate(self, raise_exception=False):

        self._validate_mapping_column_ids(raise_exception=raise_exception)
        self._validate_all_columns_mapped(raise_exception=raise_exception)

    def _validate_mapping_column_ids(self, raise_exception=False):

        # @TODO: This is draft code and not well tested.
        # See also SubTraitMapping.check_columns and TraitMapping.check_columns

        missing_columns = []
        for mapping in self._mappings:
            missing_columns.extend(mapping.check_columns(self.columns))

        if raise_exception and len(missing_columns) > 0:
            raise ValidationError("Trait Mappings of this archive reference Columns not defined in the Archive.")
        else:
            return missing_columns

    def _validate_all_columns_mapped(self, raise_exception=False):

        # @TODO: This is draft code and not well tested.

        mapped_columns = set()
        for mapping in self._mappings:
            mapped_columns.update(mapping.referenced_column_ids)

        unmapped_columns = set(self.columns) - mapped_columns

        if raise_exception and len(unmapped_columns) > 0:
            raise ValidationError("Trait Mappings of this archive reference Columns not defined in the Archive.")
        elif len(unmapped_columns) > 0:
            return unmapped_columns
        else:
            return

    def __getattr__(self, item):
        """Backup get-attr that will handle cases like a freshly loaded archive."""
        if not item.startswith("_") and self._local_trait_mappings is None and len(self._mappings) > 0:
            self.trait_mappings
            return getattr(self, item)
        else:
            raise AttributeError("Unknown attribute %s" % item)

    def __getitem__(self, key):
        # type: (str) -> AstronomicalObject
        """Make archives able to retrieve their astro-objects in the same manner as samples."""
        # Part of the "sample-like interface

        from ..astro_object import AstronomicalObject

        if key in self.contents:
            return AstronomicalObject(self, identifier=key)
        else:
            raise NotInSample("Archive '%s' does not contain object '%s'" % (self, key))

    def __iter__(self):
        """Iterate over the objects in the sample.

        Pat of the Mapping interface (collections.abc.Mapping).

        NOTE: This could be better implemented by integrating more carefully
        with the code at `self.contents`

        """

        for i in self.contents:
            yield i

    def __len__(self):
        """Number of objects in the Archive.

        Pat of the Mapping interface (collections.abc.Mapping).

        NOTE: This could be better implemented by integrating more carefully
        with the code at `self.contents`

        """

        return len(self.contents)

    def __repr__(self):
        return "FIDIAArchive:" + self.archive_id

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

def expand_column_ids_in_trait_mappings(mappings, archive_columns):
    # type: (List[Any], Dict[str, fidia_column.FIDIAColumn]) -> None
    short_to_long = None
    for mapping in mappings:
        if isinstance(mapping, fidia.traits.TraitPropertyMapping):
            mapping_column_id = fidia_column.ColumnID.as_column_id(mapping.id)
            if mapping_column_id.type == 'short':
                if short_to_long is None:
                    # Create a database of short to long IDs to make updating quick.
                    short_to_long = dict()
                    for colid in archive_columns:
                        colid = fidia_column.ColumnID.as_column_id(colid)
                        short_to_long[colid.column_type + ":" + colid.column_name] = colid
                log.debug("Replacing short ColumnID %s with full ID %s", mapping.id, short_to_long[mapping.id])
                mapping.id = short_to_long[mapping.id]
            else:
                continue
        else:
            log.debug("Recursing on mapping %s", mapping)
            expand_column_ids_in_trait_mappings(mapping, archive_columns)

class ArchiveDefinition(object):
    """A definition of the columns (data), objects, and traits (schema) making up an archive.

    This class should be subclassed to define a new Archive for use in FIDIA.
    Typically, the subclass needs to override all of the attributes.

    """


    archive_id = None
    """The ID uniquely identifying this archive (str).
     
    Typically, this will be
    composed of the Survey/Archive name. If individual instances of the
    archive may need to refer to different data (e.g., because it is stored
    in different directories, then the ID should contain this distinction in
    the form of a path or similar. If the data to be referred to is always
    the same (more typical) then the ID should not contain the path.
    
    """

    archive_type = Archive  # type: Type[Archive]
    """The class of the `.Archive` to be constructed. 
    
    `.BasePathArchive` is the most common example, which provides a base path
    abstraction to remove details of the particular local path from the rest of
    the definition of the archive.
    
    """
    writable = False

    contents = []  # type: Iterable
    """An iterable containing the names of the objects to be included in this Archive. 
        
    May be instance specific (but only if the `.archive_id` is also
    instance specific).
    
    """

    trait_mappings = []  # type: List[traits.TraitMapping]
    """List of TraitMapping objects defining the schemas of the data in this archive."""

    column_definitions = dict()  # type: Dict[str, fidia_column.ColumnDefinition]
    """List of definitions of the columns of data to be included in this archive. 
        
    When the `.ArchiveDefinition` factory creates an instances of
    an `.Archive`, these definitions will be interpreted into actual
    references to columns of data.
    
    """

    is_persisted = True
    """Does FIDIA write Archive instances from this definition into the MappingDB. 
        
    Typically only set to False for testing.
    
    """

    def __init__(self, **kwargs):
        # __init__ of superclasses not called.
        pass

    # noinspection PyProtectedMember
    def __new__(cls, **kwargs):
        # type: (Any) -> Archive
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
            archive._update_trait_pointers()

            archive._db_archive_class = fidia_classname(archive)

            # Columns
            column_definitions = deepcopy(definition.column_definitions)  # type: List[Tuple[str, fidia_column.ColumnDefinition]]

            # Associate column instances with this archive instance
            alias_mappings = dict()
            for alias, column in column_definitions:
                log.debug("Associating column %s with archive %s", column, archive)
                instance_column = column.associate(archive)
                archive.columns[instance_column.id] = instance_column
                alias_mappings[alias] = instance_column.id

            # Update any columns that have been referred to by an alias:
            replace_aliases_trait_mappings(archive._mappings, alias_mappings)

            # Update short column ids in mappings to point to local columns where possible
            expand_column_ids_in_trait_mappings(archive._mappings, archive.columns)

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

    def remove_archive(self, archive_id):
        archive = self.by_id[archive_id]
        log.info("Deleting Archive \"%s\" from the persistence database", str(archive))

        fidia.mappingdb_session.delete(archive)

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

