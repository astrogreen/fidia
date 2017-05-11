from __future__ import absolute_import, division, print_function, unicode_literals

import tempfile

# noinspection PyUnresolvedReferences
import generate_test_data as testdata
import pytest

from fidia.column.column_definitions import ColumnDefinition, FITSDataColumn
from fidia.column.columns import FIDIAColumn, ColumnID


@pytest.yield_fixture(scope='module')
def test_data_dir():

    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir


@pytest.fixture(scope='module')
def archive():
    class Archive(object):
        pass
    ar = Archive()
    ar.archive_id = 'Archive123'
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

        assert col.archive is archive
        assert col._archive_id == 'Archive123'

    def test_new_column_has_working_retriever_from_colum_definition(self, archive):
        class MyColumnDef(ColumnDefinition):
            def __init__(self, param):
                self.param = param
            column_type = FIDIAColumn
            def object_getter(self, archive, object_id):
                return "{id}: {obj} ({coldef})".format(id=archive.archive_id, obj=object_id, coldef=self.param)

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