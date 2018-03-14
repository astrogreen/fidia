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