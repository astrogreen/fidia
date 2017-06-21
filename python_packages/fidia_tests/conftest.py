import pytest

import tempfile

# noinspection PyUnresolvedReferences
import generate_test_data as testdata

@pytest.yield_fixture(scope='session')
def test_data_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir
