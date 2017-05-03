# noinspection PyUnresolvedReferences
import generate_test_data as testdata
import pytest

import tempfile

import numpy as np

import fidia
from fidia.archive.example_archive import ExampleArchive


@pytest.yield_fixture(scope='module')
def test_data_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        testdata.generate_simple_dataset(tempdir, 5)

        yield tempdir

class TestBasicExamples:


    def test_example_archive(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)

    def test_sample_creation_from_archive(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)

    def test_get_an_astro_object(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        an_object_id = next(iter(sample.keys()))
        sample[an_object_id]

    def test_get_data(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        image_data = sample['Gal1'].image['red'].data

        assert isinstance(image_data, np.ndarray)
        assert image_data.ndim == 2


# class TestMoreExamples:
#     @pytest.fixture
#     def example_archive(self):
#         return ExampleArchive(basepath=test_data_dir)
