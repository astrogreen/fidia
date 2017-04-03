from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

import tempfile

import numpy as np

from . import generate_test_data as testdata

from fidia.traits.fidiacolumn import *


@pytest.yield_fixture(scope='module')
def test_data_dir():

    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir


class TestArrayColumn:

    def test_array_column_from_data(self):
        data = np.random.random((3,5,4))

        column = ArrayColumnFromData("myid", range(3), data)

        print(data)
        print(column.ndarray)

        assert np.array_equal(data, column.ndarray)

class TestColumnFromData:

    def test_column_from_data_creation(self):
        data = np.random.random((2,))

        column = ColumnFromData(data)

        assert np.array_equal(data, column.data)

class TestFITSDataColumn:

    def test_create_column_from_data(self, test_data_dir):

        column = FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0)

        column.archive_id = 'test'
        column.basepath = test_data_dir

        data = column.get_value('Gal1')

        assert data.shape == (200, 200)
