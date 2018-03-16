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

import numpy as np
import pandas as pd
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

    @pytest.mark.parametrize('create_sample', [True, False])
    def test_get_full_sample_data(self, test_data_dir, create_sample):
        ea = ExampleArchive(basepath=test_data_dir)
        if create_sample:
            sample = fidia.Sample.new_from_archive(ea)
        else:
            sample = ea
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        image_data = sample.image['red'].data

        print(image_data)
        for d in image_data:
            assert isinstance(d, np.ndarray)
            assert d.ndim == 2

        assert len(list(image_data)) == len(ea.contents)

    @pytest.mark.parametrize('create_sample', [True, False])
    def test_get_full_sample_data_subtrait(self, test_data_dir, create_sample):
        ea = ExampleArchive(basepath=test_data_dir)
        assert isinstance(ea, fidia.Archive)
        if create_sample:
            sample = fidia.Sample.new_from_archive(ea)
        else:
            sample = ea
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        wcs = sample.image['red'].wcs

        print(wcs)
        for w in wcs:
            assert isinstance(w, fidia.Trait)
            print(w)
            print(w.cdelt1)
            assert isinstance(w.cdelt1, (int, float))

            assert w.cdelt1 == sample[w.object_id].image['red'].wcs.cdelt1


        assert len(list(wcs)) == len(ea.contents)


    @pytest.mark.parametrize('create_sample', [True, False])
    def test_get_full_sample_data_on_trait_collection(self, test_data_dir, create_sample):
        ea = ExampleArchive(basepath=test_data_dir)
        if create_sample:
            sample = fidia.Sample.new_from_archive(ea)
        else:
            sample = ea
        # an_object_id = sample.contents[0]
        # an_object_id = 'Gal1'
        mass_data = sample.dmu['StellarMasses'].table['StellarMasses'].stellar_mass
        print(mass_data)
        assert isinstance(mass_data, pd.Series)

        assert len(mass_data) == len(ea.contents)

        print(ea.contents)

        for id, value in zip(ea.contents, mass_data):
            assert sample[id].dmu['StellarMasses'].table['StellarMasses'].stellar_mass == value

        sfr_data = sample.dmu['StellarMasses'].table['StarFormationRates'].sfr
        print(sfr_data)
        assert isinstance(sfr_data, pd.Series)
        for id, value in zip(ea.contents, sfr_data):
            if np.isnan(value):
                assert np.isnan(sample[id].dmu['StellarMasses'].table['StarFormationRates'].sfr)
            else:
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

            print("archive_path = %s" % ea.basepath)

            input_data = fits.open(file_path)

            assert (input_data[0].data == image_data).all()

# class TestMoreExamples:
#     @pytest.fixture
#     def example_archive(self):
#         return ExampleArchive(basepath=test_data_dir)
