import pytest

import random
import numpy
import fidia
from fidia.archive import sami

from fidia.traits.utilities import TraitKey
from fidia.traits.abstract_base_traits import AbstractBaseTrait

class TestSAMIArchive:



    @pytest.fixture
    def sami_archive(self):
        ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
                                  "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
                                  "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
        return ar

    @pytest.fixture
    def sami_sample(self, sami_archive):
        return sami_archive.get_full_sample()

    def test_lzifu_velocity_map(self, sami_sample):
        vmap = sami_sample['28860']['velocity_map']

        assert isinstance(vmap.value, numpy.ndarray)

        assert vmap.shape() == (50, 50)
