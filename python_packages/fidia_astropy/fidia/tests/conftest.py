# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import pytest

import tempfile

# from . import generate_test_data as testdata


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# @pytest.yield_fixture(scope='session')
# def test_data_dir():
#     """Create a test dataset and yield the temp directory containing it.
#
#     This fixture is a duplicate of that in the conftest.py of the base fidia
#     package. It is duplicated here to make running tests within the test directory simple.
#
#     """
#     with tempfile.TemporaryDirectory() as tempdir:
#         testdata.generate_simple_dataset(tempdir, 5)
#
#         yield tempdir

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
