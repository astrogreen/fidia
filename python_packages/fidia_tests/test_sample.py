import pytest

import tempfile

# noinspection PyUnresolvedReferences
import generate_test_data as testdata

import fidia
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

    @pytest.mark.xfail  # No data not available in example archive.
    def test_attempt_retrieve_data_not_available(self, example_archive_sample):
        with pytest.raises(fidia.DataNotAvailable):
            example_archive_sample['Gal2']['spectral_map']

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

