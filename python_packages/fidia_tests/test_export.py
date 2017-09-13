from __future__ import absolute_import, division, print_function, unicode_literals

import tempfile
from io import BytesIO

import numpy as np
from astropy.io import fits

# noinspection PyUnresolvedReferences
import generate_test_data as testdata
import pytest

# import fidia
from fidia.archive.example_archive import ExampleArchive
from fidia.traits import *


@pytest.fixture(scope='module')
def example_archive(test_data_dir):
    return ExampleArchive(basepath=test_data_dir)

class TestFITSExport:

    def test_export_fits_file_trait(self, example_archive):
        # type: (ExampleArchive) -> None


        trait = example_archive['Gal1'].fits_file['red_image']
        assert isinstance(trait, FITSFile)

        file_bytes = BytesIO()

        trait.export_as_fits(file_bytes)

        file_bytes.seek(0)

        fits_file = fits.open(file_bytes)

        fits_file.verify('exception')

        print(fits_file.info())

        assert isinstance(fits_file[0].data, np.ndarray)

        image_trait = trait.fits_image_hdu["PRIMARY"]
        assert (fits_file[0].data == image_trait.data).all()

        print(fits_file[0].header.tostring('\n', endcard=False, padding=False))

        header = image_trait.fits_header["header"]
        for tp_name in header.dir_trait_properties():

            assert fits_file[0].header[tp_name] == getattr(header, tp_name)
