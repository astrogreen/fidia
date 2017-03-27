from __future__ import absolute_import, division, print_function, unicode_literals

import pytest


import numpy as np

from fidia.traits.fidiacolumn import *

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

        column = ColumnFromData("myid", range(3), data)


        assert np.array_equal(data, column)
