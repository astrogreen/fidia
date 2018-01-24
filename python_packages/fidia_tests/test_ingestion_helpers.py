# noinspection PyUnresolvedReferences
import pytest

from typing import Tuple, List, Dict

import os
import tempfile
import subprocess
import warnings

import numpy as np
# from astropy.io import fits

import fidia
from fidia.ingest.data_finder import finder_fits_file

@pytest.fixture(scope="module")
def finder_fits_file_results(test_data_dir):
    columns_found, fits_mapping = finder_fits_file(
        "{object_id}/{object_id}_red_image.fits", object_id="Gal1",
        basepath=test_data_dir
    )

    return columns_found, fits_mapping

def test_finder_fits_data_types(finder_fits_file_results):

    columns_found, fits_mapping = finder_fits_file_results  # type: Tuple[List[fidia.ColumnDefinition], List[fidia.traits.TraitMapping]]

    # print(columns_found)

    columns = {c.id: c for c in columns_found}  # type: Dict[str, fidia.ColumnDefinition]

    for k in columns:
        print(
            "{0.id}  {0.dtype}".format(
                columns[k]
            )
        )



    assert columns["FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[PRIMARY].header[NAXIS]"].dtype == "int64"
    assert columns["FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[PRIMARY].header[NAXIS1]"].dtype == "int64"
    assert columns["FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[PRIMARY].header[NAXIS2]"].dtype == "int64"
    assert columns["FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[PRIMARY].header[CRPIX1]"].dtype == "float64"
    assert columns["FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[PRIMARY].header[TELESCOP]"].dtype == str


    # assert False