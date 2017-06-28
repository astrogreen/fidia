import pytest

import os.path
import tempfile

from astropy.io import fits
import numpy as np

from fidia.traits import *
from fidia.exceptions import DataNotAvailable
from fidia import Sample
from fidia.archive.example_archive import ExampleArchive, ExampleSpectralMap, ExampleSpectralMapExtra


def test_fits_creation():
    """Basic test of functionality. If this doesn't work, all other tests are invalid."""
    example_sample = ExampleArchive().get_full_sample()

    image_trait = example_sample['Gal1']['image-blue']

    with tempfile.TemporaryDirectory() as tempdir:
        filename = tempdir + "/image-blue.fits"
        image_trait.as_fits(filename)

        assert os.path.exists(filename)

class TestFITSExport:

    @pytest.fixture
    def example_sample(self):
        return ExampleArchive().get_full_sample()

    @pytest.fixture
    def image_trait(self, example_sample):
        return example_sample['Gal1']['image-blue']

    @pytest.yield_fixture
    def image_hdu_list(self, example_sample):

        image_trait = example_sample['Gal1']['image-blue']

        with tempfile.TemporaryDirectory() as tempdir:
            filename = tempdir + "/image-blue.fits"
            image_trait.as_fits(filename)
            hdu_list = fits.open(filename, memmap=True)
            yield hdu_list


    def test_fits_file_valid(self, image_hdu_list):
        # type (fits.HDUList) -> None
        image_hdu_list.verify('exception')

    def test_fits_for_image_trait_contains_data(self, image_hdu_list, image_trait):
        # type (fits.HDUList, Trait) -> None

        assert isinstance(image_hdu_list[0].data, np.ndarray)

        assert (image_hdu_list[0].data == image_trait.value()).all()

    def test_fits_for_image_has_variance_data(self, image_hdu_list, image_trait):
        # type (fits.HDUList, Trait) -> None

        print(image_hdu_list.info())

        image_hdu_list['VARIANCE']

        data = image_hdu_list['VARIANCE'].data

        assert (data == image_trait.variance()).all()

    def test_fits_contains_single_value_trait_properties_as_header_items(self, image_hdu_list, image_trait):

        assert image_hdu_list[0].header['EXTRA_PROPERTY_BLUE'] == 'blue'

    def test_meta_data_added_to_fits_header(self, image_hdu_list):

        print(image_hdu_list[0].header.tostring('\n', endcard=False, padding=False))

        assert image_hdu_list[0].header['DETECTOR'] == 'DETECTOR'

        assert image_hdu_list[0].header['GAIN'] == 0.3