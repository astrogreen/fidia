"""
These tests check that the database parts of FIDIA are working as expected.

"""

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestDatabaseBasics:

    @pytest.fixture
    def engine(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        # engine = create_engine('sqlite:////Users/agreen/Desktop/fidia.sql', echo=True)

        from fidia.base_classes import SQLAlchemyBase
        SQLAlchemyBase.metadata.create_all(engine)

        return engine

    @pytest.fixture
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
