import pytest

import os.path
import tempfile

from astropy.io import fits

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

    @pytest.yield_fixture
    def image_fits(self):
        example_sample = ExampleArchive().get_full_sample()

        image_trait = example_sample['Gal1']['image-blue']

        with tempfile.TemporaryDirectory() as tempdir:
            filename = tempdir + "/image-blue.fits"
            image_trait.as_fits(filename)
            yield filename


    def test_fits_file_valid(self, image_fits):
        # type (Sample) -> None

        ff = fits.open(image_fits, memmap=True)

        ff.verify('exception')