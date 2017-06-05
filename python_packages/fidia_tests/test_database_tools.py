"""
These tests check that the database parts of FIDIA are working as expected.

"""

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fidia.utilities import *


class TestDatabaseBasics:

    @pytest.fixture
    def engine(self):
        engine = create_engine('sqlite:///:memory:', echo=True)
        return engine

    @pytest.fixture
    def session(self, engine):
        Session = sessionmaker(bind=engine)
        return Session()

    def test_trait_property_mapping(self, session, engine):
        from fidia.traits.trait_utilities import TraitPropertyMapping, Base

        Base.metadata.create_all(engine)

        tpm = TraitPropertyMapping('my_test_ctype2',
                             'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE2]:1')
        session.add(tpm)
        #session.commit()

        del tpm

        # The data has been pushed to the database and removed from Python. Now
        # try to reload the data from the DB.


        tpm = session.query(TraitPropertyMapping).filter_by(name='my_test_ctype2').one()
        print(tpm)
        assert tpm.id == 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE2]:1'
        assert tpm.name == 'my_test_ctype2'

        session.rollback()

    def test_trait_mapping(self, session, engine):

        from fidia.traits import TraitMapping, TraitPropertyMapping, Image, TraitKey
        from fidia.traits.trait_utilities import Base

        Base.metadata.create_all(engine)

        tm = TraitMapping(Image, "red", [
            TraitPropertyMapping('data', "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"),
            TraitPropertyMapping('exposed', "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1")]
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
            assert item.id in ("ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1",
                               "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1")
            if item.name == "data":
                assert item.id == "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"

        # assert False

