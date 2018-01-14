# noinspection PyUnresolvedReferences
import generate_test_data as testdata
import pytest

import tempfile

import numpy as np
from astropy.io import fits

import fidia
from fidia.archive.example_archive import ExampleArchive

# Pytest fixture 'test_data_dir' now session wide and stored in conftest.py
# @pytest.yield_fixture(scope='module')
# def test_data_dir():
#     with tempfile.TemporaryDirectory() as tempdir:
#         testdata.generate_simple_dataset(tempdir, 5)
#
#         yield tempdir

class TestBasicExamples:


    def test_example_archive(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)

    def test_sample_creation_from_archive(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)

    def test_sample_contents(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        print(ea.contents)

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

    def test_get_data_subtrait(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        wcs = sample['Gal1'].image['red'].wcs

        print(wcs)
        assert isinstance(wcs, fidia.Trait)
        print(wcs.cdelt1)
        assert isinstance(wcs.cdelt1, (int, float))

    def test_get_data_on_trait_collection(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        mass = sample['Gal1'].dmu['StellarMasses'].table['StellarMasses'].stellar_mass
        print(mass)
        assert isinstance(mass, (int, float))

        sfr = sample['Gal1'].dmu['StellarMasses'].table['StarFormationRates'].sfr
        print(sfr)
        assert isinstance(sfr, (int, float))

    def test_get_full_sample_data(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        image_data = sample.image['red'].data

        print(image_data)
        for d in image_data:
            assert isinstance(d, np.ndarray)
            assert d.ndim == 2

        assert len(list(image_data)) == len(ea.contents)

    def test_get_full_sample_data_subtrait(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        wcs = sample.image['red'].wcs

        print(wcs)
        for w in wcs:
            assert isinstance(w, fidia.Trait)
            print(w.cdelt1)
            assert isinstance(w.cdelt1, (int, float))

        assert len(list(wcs)) == len(ea.contents)


    def test_get_full_sample_data_on_trait_collection(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        mass_data = sample.dmu['StellarMasses'].table['StellarMasses'].stellar_mass
        print(mass_data)
        assert isinstance(mass_data, np.ndarray)

        assert len(mass_data) == len(ea.contents)

        for id, value in zip(ea.contents, mass_data):
            assert sample[id].dmu['StellarMasses'].table['StellarMasses'].stellar_mass == value

        sfr_data = sample.dmu['StellarMasses'].table['StarFormationRates'].sfr
        print(sfr_data)
        assert isinstance(sfr_data, np.sfr_data)
        for id, value in zip(ea.contents, mass_data):
            assert sample[id].dmu['StellarMasses'].table['StarFormationRates'].sfr == value



    def test_get_an_astro_object_from_archive(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        # an_object_id = next(iter(sample.keys()))
        an_object_id = 'Gal1'
        astro_object = ea[an_object_id]
        assert isinstance(astro_object, fidia.AstronomicalObject)

        sfr = astro_object.dmu['StellarMasses'].table['StarFormationRates'].sfr
        print(sfr)
        assert isinstance(sfr, (int, float))


class TestDataIntegrity:

    def test_output_matches_input(self, test_data_dir):
        ea = ExampleArchive(basepath=test_data_dir)
        sample = fidia.Sample.new_from_archive(ea)
        for an_object_id in sample.ids:
            print("an_object_id = %s" % an_object_id)
            image_data = sample[an_object_id].image['red'].data

            file_path = test_data_dir + "/{object_id}/{object_id}_red_image.fits".format(object_id=an_object_id)
            print("file_path = %s" % file_path)

            input_data = fits.open(file_path)

            assert (input_data[0].data == image_data).all()

# class TestMoreExamples:
#     @pytest.fixture
#     def example_archive(self):
#         return ExampleArchive(basepath=test_data_dir)
