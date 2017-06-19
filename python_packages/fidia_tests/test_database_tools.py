"""
These tests check that the database parts of FIDIA are working as expected.

"""

import pytest


@pytest.fixture(scope='function')
def engine():
    engine = create_engine('sqlite:///:memory:', echo=True)
    # engine = create_engine('sqlite:////Users/agreen/Desktop/fidia.sql', echo=True)
    
    from fidia.base_classes import SQLAlchemyBase
    SQLAlchemyBase.metadata.create_all(engine)

    return engine


class TestDatabaseBasics:

    @pytest.fixture(scope='function')
    def session(self, engine):
        Session = sessionmaker(bind=engine)
        return Session()

    def test_trait_property_mapping(self, session, engine):
        from fidia.traits.trait_utilities import TraitPropertyMapping

        tpm = TraitPropertyMapping(
            'my_test_ctype2',
            'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE2]:1')
        session.add(tpm)

        del tpm

        # The data has been pushed to the database and removed from Python. Now
        # try to reload the data from the DB.


        tpm = session.query(TraitPropertyMapping).filter_by(name='my_test_ctype2').one()
        print(tpm)
        assert tpm.id == 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE2]:1'
        assert tpm.name == 'my_test_ctype2'

        session.rollback()

    def test_simple_trait_mapping(self, session, engine):

        from fidia.traits import TraitMapping, TraitPropertyMapping, Image, TraitKey

        tm = TraitMapping(Image, "red", [
            TraitPropertyMapping('data', "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"),
            TraitPropertyMapping(
                'exposed',
                "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1")]
        )

        session.add(tm)
        session.commit()

        del tm

        # The data has been pushed to the database and removed from Python. Now
        # try to reload the data from the DB.


        tm = session.query(TraitMapping).filter_by(_db_trait_key="red").one()
        assert isinstance(tm, TraitMapping)
        print(tm)
        assert tm.trait_class is Image
        assert tm.trait_key == TraitKey("red")

        for item in tm.trait_property_mappings.values():
            assert isinstance(item, TraitPropertyMapping)
            assert item.name in ("data", "exposed")
            assert item.id in (
                "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1",
                "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1")
            if item.name == "data":
                assert item.id == "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"

                # assert False

    def test_sub_trait_mapping(self, session, engine):
        from fidia.traits.trait_utilities import SubTraitMapping, TraitPropertyMapping
        from fidia.traits import ImageWCS

        stm = SubTraitMapping(
            'wcs', ImageWCS, [
                TraitPropertyMapping(
                    'crpix1',
                    'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL1]:1'),
                TraitPropertyMapping('crpix2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL2]:1'),
            ]
        )
        session.add(stm)

        del stm

        # The data has been pushed to the database and removed from Python. Now
        # try to reload the data from the DB.


        stm = session.query(SubTraitMapping).filter_by(name='wcs').one()
        print(stm)
        assert isinstance(stm, SubTraitMapping)
        assert stm.trait_class is ImageWCS
        assert stm.name == "wcs"

        session.rollback()


    def test_trait_mapping_with_subtraits(self, session, engine):

        from fidia.traits import TraitMapping, TraitPropertyMapping, Image, TraitKey, SubTraitMapping, ImageWCS

        tm = TraitMapping(
            Image, 'redsubtrait', [
                TraitPropertyMapping('data', "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"),
                TraitPropertyMapping('exposed', "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1"),
                SubTraitMapping(
                    'wcs', ImageWCS, [
                        TraitPropertyMapping('crpix1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL1]:1'),
                        TraitPropertyMapping('crpix2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL2]:1'),
                    ]
                )
            ]
        )

        session.add(tm)
        session.commit()

        del tm

        # The data has been pushed to the database and removed from Python. Now
        # try to reload the data from the DB.


        tm = session.query(TraitMapping).filter_by(_db_trait_key="redsubtrait").one()
        assert isinstance(tm, TraitMapping)
        print(tm)
        assert tm.trait_class is Image
        assert tm.trait_key == TraitKey("redsubtrait")

        for item in tm.trait_property_mappings.values():
            assert isinstance(item, TraitPropertyMapping)
            assert item.name in ("data", "exposed")
            assert item.id in ("ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1",
                               "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1")
            if item.name == "data":
                assert item.id == "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"

        wcs = tm.sub_trait_mappings["wcs"]
        assert isinstance(wcs, SubTraitMapping)
        assert wcs.trait_class is ImageWCS
        assert wcs.name == "wcs"
        tp = wcs.trait_property_mappings['crpix1']
        assert isinstance(tp, TraitPropertyMapping)
        assert tp.id == 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL1]:1'

    def test_trait_collection_mapping(self, session, engine):

        from fidia.traits import TraitMapping, TraitPropertyMapping, DMU, Table, TraitKey

        tm = TraitMapping(
            DMU, 'StellarMasses', [
                TraitMapping(Table, 'StellarMasses', [
                    TraitPropertyMapping('stellar_mass', 'ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[StellarMass]:1'),
                    TraitPropertyMapping('stellar_mass_error', 'ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[StellarMassError]:1')
                ]),
                TraitMapping(Table, 'StarFormationRates', [
                    TraitPropertyMapping('sfr', 'ExampleArchive:FITSBinaryTableColumn:sfr_table.fits[1].data[SFR]:1'),
                    TraitPropertyMapping('sfr_err', 'ExampleArchive:FITSBinaryTableColumn:sfr_table.fits[1].data[SFR_ERR]:1')
                ])
            ]
        )

        session.add(tm)
        session.commit()

        del tm

        # The data has been pushed to the database and removed from Python. Now
        # try to reload the data from the DB.


        tm = session.query(TraitMapping).filter_by(_db_trait_key="StellarMasses", _parent_id=None).one()
        assert isinstance(tm, TraitMapping)
        print(tm)
        assert tm.trait_class is DMU
        assert tm.trait_key == TraitKey("StellarMasses")

        for item in tm.named_sub_mappings.values():
            assert isinstance(item, TraitMapping)
            assert item.trait_class is Table
            assert str(item.trait_key) in ("StellarMasses", "StarFormationRates")
            if item.trait_key == "StellarMasses":
                for tp in item.trait_property_mappings.values():
                    assert isinstance(tp, TraitPropertyMapping)
                    tp.name in ("stellar_mass", "stellar_mass_err")

    def test_archive_persistance_in_db(self, session, engine):
        from fidia.archive import BasePathArchive
        from fidia.traits import TraitMapping, Image, TraitPropertyMapping
        from fidia.column import FITSDataColumn


        class ArchiveWithColumns(BasePathArchive):
            _id = "testArchive"
            column_definitions = [
                ("col", FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0,
                                       ndim=2,
                                       timestamp=1))
            ]

            trait_mappings = [
                TraitMapping(Image, "red", [
                    TraitPropertyMapping('data',
                                         "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"),
                    TraitPropertyMapping(
                        'exposed',
                        "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1")]
                             )
            ]

        ar = ArchiveWithColumns(basepath='')

        #
        #
        # del stm
        #
        # # The data has been pushed to the database and removed from Python. Now
        # # try to reload the data from the DB.
        #
        #
        # stm = session.query(SubTraitMapping).filter_by(name='wcs').one()
        # print(stm)
        # assert isinstance(stm, SubTraitMapping)
        # assert stm.trait_class is ImageWCS
        # assert stm.name == "wcs"
        #
        # session.rollback()
from sqlalchemy import create_engine


from sqlalchemy.orm import sessionmaker

from fidia.database_tools import is_sane_database
from sqlalchemy import engine_from_config, Column, Integer, String
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import ForeignKey


def gen_test_model():
    Base = declarative_base()

    class SaneTestModel(Base):
        """A sample SQLAlchemy model to demostrate db conflicts. """

        __tablename__ = "sanity_check_test"

        #: Running counter used in foreign key references
        id = Column(Integer, primary_key=True)

    return Base, SaneTestModel


def gen_relation_models():
    Base = declarative_base()

    class RelationTestModel(Base):
        __tablename__ = "sanity_check_test_2"
        id = Column(Integer, primary_key=True)

    class RelationTestModel2(Base):
        __tablename__ = "sanity_check_test_3"
        id = Column(Integer, primary_key=True)

        test_relationship_id = Column(ForeignKey("sanity_check_test_2.id"))
        test_relationship = relationship(RelationTestModel, primaryjoin=test_relationship_id == RelationTestModel.id)

    return Base, RelationTestModel, RelationTestModel2


def gen_declarative():
    Base = declarative_base()

    class DeclarativeTestModel(Base):
        __tablename__ = "sanity_check_test_4"
        id = Column(Integer, primary_key=True)

        @declared_attr
        def _password(self):
            return Column('password', String(256), nullable=False)

        @hybrid_property
        def password(self):
            return self._password

    return Base, DeclarativeTestModel


class TestIsSaneDatabase:

    """Tests for checking database sanity checks functions correctly."""



    def test_sanity_pass(self, engine):
        """See database sanity check completes when tables and columns are created."""

        conn = engine.connect()
        trans = conn.begin()

        Base, SaneTestModel = gen_test_model()
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            Base.metadata.drop_all(engine, tables=[SaneTestModel.__table__])
        except sqlalchemy.exc.NoSuchTableError:
            pass

        Base.metadata.create_all(engine, tables=[SaneTestModel.__table__])

        try:
            assert is_sane_database(Base, session) is True
        finally:
            Base.metadata.drop_all(engine)


    def test_sanity_table_missing(self, engine):
        """See check fails when there is a missing table"""

        conn = engine.connect()
        trans = conn.begin()

        Base, SaneTestModel = gen_test_model()
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            Base.metadata.drop_all(engine, tables=[SaneTestModel.__table__])
        except sqlalchemy.exc.NoSuchTableError:
            pass

        assert is_sane_database(Base, session) is False


    # This test fails because SQLite doesn't support the DROP COLUMN syntax.
    @pytest.mark.xfail
    def test_sanity_column_missing(self, engine):
        """See check fails when there is a missing table"""

        conn = engine.connect()
        trans = conn.begin()

        Session = sessionmaker(bind=engine)
        session = Session()
        Base, SaneTestModel = gen_test_model()
        try:
            Base.metadata.drop_all(engine, tables=[SaneTestModel.__table__])
        except sqlalchemy.exc.NoSuchTableError:
            pass
        Base.metadata.create_all(engine, tables=[SaneTestModel.__table__])

        # Delete one of the columns
        engine.execute("ALTER TABLE sanity_check_test DROP COLUMN id")

        # engine.execute("""
        # BEGIN TRANSACTION;
        #
        # ALTER TABLE equipment RENAME TO temp_equipment;
        #
        # CREATE TABLE equipment (
        #  name text NOT NULL,
        #  model text NOT NULL,
        #  serial integer NOT NULL UNIQUE
        # );
        #
        # INSERT INTO equipment
        # SELECT
        #  name, model, serial
        # FROM
        #  temp_equipment;
        #
        # DROP TABLE temp_equipment;
        #
        # COMMIT;
        #
        # """)

        assert is_sane_database(Base, session) is False


    def test_sanity_pass_relationship(self, engine):
        """See database sanity check understands about relationships and don't deem them as missing column."""

        conn = engine.connect()
        trans = conn.begin()

        Session = sessionmaker(bind=engine)
        session = Session()

        Base, RelationTestModel, RelationTestModel2  = gen_relation_models()
        try:
            Base.metadata.drop_all(engine, tables=[RelationTestModel.__table__, RelationTestModel2.__table__])
        except sqlalchemy.exc.NoSuchTableError:
            pass

        Base.metadata.create_all(engine, tables=[RelationTestModel.__table__, RelationTestModel2.__table__])

        try:
            assert is_sane_database(Base, session) is True
        finally:
            Base.metadata.drop_all(engine)


    def test_sanity_pass_declarative(self, engine):
        """See database sanity check understands about relationships and don't deem them as missing column."""

        conn = engine.connect()
        trans = conn.begin()

        Session = sessionmaker(bind=engine)
        session = Session()

        Base, DeclarativeTestModel = gen_declarative()
        try:
            Base.metadata.drop_all(engine, tables=[DeclarativeTestModel.__table__])
        except sqlalchemy.exc.NoSuchTableError:
            pass

        Base.metadata.create_all(engine, tables=[DeclarativeTestModel.__table__])

        try:
            assert is_sane_database(Base, session) is True
        finally:
            Base.metadata.drop_all(engine)