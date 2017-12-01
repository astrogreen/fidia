import pytest

import tempfile

# noinspection PyUnresolvedReferences
import generate_test_data as testdata


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.yield_fixture(scope='session')
def test_data_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir

@pytest.fixture(scope='function')
def clean_persistence_database(monkeypatch):

    import fidia

    # Create a completely clean database

    engine = create_engine('sqlite:///:memory:', echo=False)

    from fidia.base_classes import SQLAlchemyBase
    SQLAlchemyBase.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    monkeypatch.setattr(fidia, 'mappingdb_session', session)
