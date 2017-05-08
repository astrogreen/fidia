# noinspection PyUnresolvedReferences
import generate_test_data as testdata
import pytest

import tempfile

import numpy as np
from astropy.io import fits

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

        print(image_data)
        assert isinstance(image_data, np.ndarray)
        assert image_data.ndim == 2

        exposed = sample['Gal1'].image['red'].exposed

        print(exposed)
        assert isinstance(exposed, (int, float))

        cube_data = sample['Gal1'].spectral_cube['red'].data

        print(cube_data)
        assert isinstance(cube_data, np.ndarray)
        assert cube_data.ndim == 3

class TestDataIntegrity:

    def test_output_matches_input(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        for an_object_id in sample.ids:
            image_data = sample[an_object_id].image['red'].data

            file_path = test_data_dir + "/{object_id}/{object_id}_red_image.fits".format(object_id=an_object_id)

            input_data = fits.open(file_path)

            assert (input_data[0].data == image_data).all()

# class TestMoreExamples:
#     @pytest.fixture
#     def example_archive(self):
#         return ExampleArchive(basepath=test_data_dir)
