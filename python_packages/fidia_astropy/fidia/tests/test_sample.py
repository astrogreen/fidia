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

# noinspection PyUnresolvedReferences
from . import generate_test_data as testdata

import fidia
import fidia.exceptions
from fidia import Sample, AstronomicalObject
# from fidia.archive import MemoryArchive
from fidia.archive.example_archive import ExampleArchive

# Pytest fixture 'test_data_dir' now session wide and stored in conftest.py
# @pytest.yield_fixture(scope='module')
# def test_data_dir():
#     with tempfile.TemporaryDirectory() as tempdir:
#         testdata.generate_simple_dataset(tempdir, 5)
#
#         yield tempdir

class TestSample:


    @pytest.fixture
    def empty_sample(self):
        empty_sample = Sample()
        return empty_sample

    # @pytest.fixture
    # def writeable_sample(self):
    #     mysample = Sample()
    #     mysample.add_from_archive(MemoryArchive())
    #     return mysample

    @pytest.fixture
    def example_archive_sample(self, test_data_dir):
        ar = ExampleArchive(basepath=test_data_dir)
        sample = Sample.new_from_archive(ar)
        return sample

    def test_new_sample_has_no_archives(self, empty_sample):
        assert len(empty_sample.archives) == 0

    def test_new_sample_is_read_only(self, empty_sample):
        assert empty_sample.read_only 

    def test_sample_behaves_like_dict(self, example_archive_sample):

        example_archive_sample.keys()
        len(example_archive_sample)

        for key in example_archive_sample:
            assert isinstance(key, str)

        for key in example_archive_sample.keys():
            assert isinstance(key, str)

    def test_attempt_retrieve_data_not_available(self, example_archive_sample):
        # First check that data is available for this trait where expected:
        cube = example_archive_sample['Gal2'].spectral_cube["red"].data
        print(cube)

        with pytest.raises(fidia.exceptions.DataNotAvailable):
            cube = example_archive_sample['Gal3'].spectral_cube["red"].data
            print(cube)

                    # Tests for a writeable Sample
    #   Commented out as writeable samples are not currently required.

    # def test_add_items_via_dictionary(self, writeable_sample):
    #     writeable_sample['gal1']
    #     assert 'gal1' in writeable_sample.keys()
    #     assert isinstance(writeable_sample['gal1'], AstronomicalObject)
    #     writeable_sample['gal1'].redshift = 0.6
    #     assert writeable_sample['gal1'].redshift == 0.6
    #
    #
    # def test_add_items_via_dictionary_with_assignment(self, writeable_sample):
    #     writeable_sample['gal2'].redshift = 0.453
    #     assert writeable_sample['gal2'].redshift == 0.453
    #     assert 'gal2' in writeable_sample.keys()
    #
    # def test_property_updatable_on_writeable_archive(self, writeable_sample):
    #     writeable_sample['gal2'].redshift = 0.453
    #     assert writeable_sample['gal2'].redshift == 0.453
    #     writeable_sample['gal1'].redshift = 0.532
    #     assert writeable_sample['gal1'].redshift == 0.532

