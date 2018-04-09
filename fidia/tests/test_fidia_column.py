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

from __future__ import absolute_import, division, print_function, unicode_literals

import tempfile

import re

# from . import generate_test_data as testdata
import pytest

import fidia
from fidia.column.column_definitions import ColumnDefinition, FITSDataColumn, FITSBinaryTableColumn, CSVTableColumn, \
    FITSHeaderColumn
from fidia.column.columns import FIDIAColumn, ColumnID
from fidia import ArchiveDefinition

# Pytest fixture 'test_data_dir' now session wide and stored in conftest.py
# @pytest.yield_fixture(scope='module')
# def test_data_dir():
#
#     with tempfile.TemporaryDirectory() as tempdir:
#         testdata.generate_simple_dataset(tempdir, 5)
#
#         yield tempdir


@pytest.fixture(scope='module')
def archive():
    class MyArchive(ArchiveDefinition):
        contents = ["Gal1"]
        archive_id = 'Archive123'

    ar = MyArchive()
    return ar


class TestColumnIDs:

    @pytest.fixture
    def column_id_list(self):
        return [
            "testArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"
        ]
    # def test_column_id_creation(self):
    #     ColumnID()

    def test_column_equality(self):
        col1 = ColumnID.as_column_id("testArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1")
        col2 = ColumnID.as_column_id("testArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1")

        assert col1 == col2

    @pytest.mark.xfail
    def test_column_equality_latest(self):
        col1 = ColumnID.as_column_id("testArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1")
        col2 = ColumnID.as_column_id("testArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1")

        assert col1.replace(timestamp='latest') == col2
        assert col1 == col2.replace(timestamp='latest')


class TestColumnDefs:

    # This test fails because MyColumnDef has a weird classname which originally
    # was not part of fidia, but now is because of the location of the tests.
    @pytest.mark.xfail
    def test_column_ids_class_name(self):
        class MyColumnDef(ColumnDefinition):
            pass
        print(MyColumnDef.__module__, MyColumnDef.__name__)
        coldef = MyColumnDef()
        print(coldef.id)
        assert coldef.id.startswith(MyColumnDef.__module__ + '.' + MyColumnDef.__name__)

class TestColumnDefColumnCreation:

    def test_new_column(self, archive):
        coldef = ColumnDefinition()
        # The base ColumnDefinition does not have a defined `column_type`, so we must define one:
        coldef.column_type = FIDIAColumn
        col = coldef.associate(archive)

        # assert col.archive is archive
        # assert col._archive_id == 'Archive123'

        assert isinstance(col.id, str)
        assert re.match(r"Archive123:ColumnDefinition::[\d\.]+", col.id) is not None

    def test_new_column_has_working_retriever_from_colum_definition(self, archive):
        class MyColumnDef(ColumnDefinition):

            _id_string = "myColumn"

            _parameters = ['param']

            # def __init__(self, param):
            #     self.param = param
            column_type = FIDIAColumn

            def object_getter(self, object_id, archive_id):
                return "{id}: {obj} ({coldef})".format(id=archive_id, obj=object_id, coldef=self.param)

        coldef = MyColumnDef('test')
        col = coldef.associate(archive)
        assert col.get_value('Gal1') == "Archive123: Gal1 (test)"

    def test_associated_column_has_timestamp(self, archive):
        coldef = ColumnDefinition()
        # The base ColumnDefinition does not have a defined `column_type`, so we must define one:
        coldef.column_type = FIDIAColumn
        col = coldef.associate(archive)

        assert isinstance(col._timestamp, (float, int))

# class TestArrayColumn:
#
#     def test_array_column_from_data(self):
#         data = np.random.random((3,5,4))
#
#         column = ArrayColumnFromData("myid", range(3), data)
#
#         print(data)
#         print(column.ndarray)
#
#         assert np.array_equal(data, column.ndarray)
#
# class TestColumnFromData:
#
#     def test_column_from_data_creation(self):
#         data = np.random.random((2,))
#
#         column = ColumnFromData(data)
#
#         assert np.array_equal(data, column.data)
#
class TestFITSDataColumn:

    @pytest.fixture
    def fits_data_column(self, test_data_dir, archive):
        columndef = FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0)
        archive.basepath = test_data_dir
        column = columndef.associate(archive)
        return column

    def test_column_has_data(self, fits_data_column):
        data = fits_data_column.get_value('Gal1')
        assert data.shape == (200, 200)

    def test_column_id(self):
        pathstring = "{object_id}/{object_id}_red_image.fits"
        coldef = FITSDataColumn(pathstring, 0)
        print(coldef.id)
        assert coldef.id == "FITSDataColumn:" + pathstring + "[0]"

class TestFITSBinaryTableColumn:

    @pytest.fixture
    def fits_binary_table_column(self, test_data_dir, archive):
        column_def = FITSBinaryTableColumn("stellar_masses.fits", 1, 'StellarMass', 'ID')
        archive.basepath = test_data_dir
        column = column_def.associate(archive)
        column._archive = archive
        return column

    def test_column_has_data(self, fits_binary_table_column):
        data = fits_binary_table_column.get_value('Gal1')
        assert isinstance(data, (int, float))

class TestFITSHeaderColumn:

    @pytest.fixture
    def fits_binary_table_column(self, test_data_dir, archive):
        column_def = FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRVAL1")
        archive.basepath = test_data_dir
        column = column_def.associate(archive)
        column._archive = archive
        return column

    def test_column_has_data(self, fits_binary_table_column):
        data = fits_binary_table_column.get_value('Gal1')
        assert isinstance(data, (int, float))


class TestCSVTableColumn:

    @pytest.fixture(scope='class')
    def csv_table_column(self, test_data_dir, archive):
        column_def = CSVTableColumn("sfr_table.csv", 'SFR', 'ID', "#")
        archive.basepath = test_data_dir
        column = column_def.associate(archive)
        column._archive = archive
        return column

    def test_column_has_data(self, csv_table_column):
        data = csv_table_column.get_value('Gal1')
        assert isinstance(data, (int, float))

def test_archive_column_relationship(test_data_dir):

    class MyArchive(ArchiveDefinition):
        def __init__(self, **kwargs):
            super(MyArchive, self).__init__(**kwargs)
            self.contents = ["Gal1"]
            self.archive_id = 'Archive123'
            self.column_definitions = fidia.ColumnDefinitionList([
                CSVTableColumn("sfr_table.csv", 'SFR', 'ID', "#")
            ])

    ar = MyArchive(basepath=test_data_dir)

    for col in ar.columns.values():
        print(col)
        assert col._archive is not None
