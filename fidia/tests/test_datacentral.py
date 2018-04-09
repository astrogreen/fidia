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

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import tempfile

import numpy as np

import pytest

import fidia
from fidia.archive.adc_archive import DataCentralArchive


def test_s7_validation():
    ar = DataCentralArchive(basepath="/Users/agreen/Desktop/s7")  # type: fidia.Archive

    for col in ar.columns.values():
        print(col)
        assert col._archive is not None


    assert ar["NGC1204"].dmu["tables"].table["catalog"].RA_hms == "03 04 40.01"



    # assert False
