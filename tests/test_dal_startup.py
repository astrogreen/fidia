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

import os
import tempfile
import configparser

import numpy as np
from astropy.io import fits

import fidia
import fidia.local_config
from fidia.utilities import deindent_tripple_quoted_string
from fidia.dal import NumpyFileStore, DataAccessLayerHost

@pytest.yield_fixture(scope='module')
def dal_data_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        yield tempdir


def test_dal_creation_single_layer(dal_data_dir):
    """Test startup with a single layer which is the numpy file store."""

    config_text = fidia.local_config.DEFAULT_CONFIG + deindent_tripple_quoted_string("""
    [DAL-NumpyFileStore]
    base_path = {base_path}
    """.format(base_path=dal_data_dir))

    print(config_text)

    config = configparser.ConfigParser()
    config.read_string(config_text)

    dal_host = DataAccessLayerHost(config)

    print(dal_host)

    # assert False