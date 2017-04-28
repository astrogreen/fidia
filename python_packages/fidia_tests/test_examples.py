# noinspection PyUnresolvedReferences
import generate_test_data as testdata
import pytest

import tempfile

import fidia
from fidia.archive.example_archive import ExampleArchive

@pytest.yield_fixture(scope='module')
def test_data_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir

class TestBasicExamples:


    def test_example_archive(self):
        ea = ExampleArchive(basepath=test_data_dir)

    def test_sample_creation_from_archive(self, ):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.create_sample_from_full_archive(ea)

    def test_get_an_astro_object(self):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.create_sample_from_full_archive(ea)
        an_object_id = sample.contents[0]
        sample[an_object_id]

    def test_get_data(self):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.create_sample_from_full_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        sample['Gal1'].image['red'].data


# class TestMoreExamples:
#     @pytest.fixture
#     def example_archive(self):
#         return ExampleArchive(basepath=test_data_dir)
