import pytest


import random
import numpy
from io import BytesIO
import pickle

import fidia
from fidia.archive import sami

from fidia.traits.utilities import TraitKey
from fidia.traits.abstract_base_traits import AbstractBaseTrait


class TestSAMISerialization:



    @pytest.fixture
    def sami_archive(self):
        sami_archive = sami.SAMITeamArchive(
                                  "/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
                                  "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
                                  "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
        return sami_archive

    @pytest.fixture
    def sami_sample(self, sami_archive):
        return sami_archive.get_full_sample()

    def test_spectral_cube_serialization(self, sami_sample):
        # Collect a trait and generate a serialized version
        t = sami_sample['23117']['spectral_map', 'red']
        byte_data = t.as_bytes()

        with BytesIO(byte_data) as byte_file:
            test_dict = pickle.load(byte_file)
            for key in test_dict:
                print("Checking key '{}'".format(key))
                if isinstance(test_dict[key], numpy.ndarray):
                    numpy.testing.assert_array_equal(test_dict[key], getattr(t, key))
                else:
                    assert test_dict[key] == getattr(t, key)()
