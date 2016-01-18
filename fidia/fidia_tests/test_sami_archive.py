import pytest

import numpy

import fidia
from fidia.archive import sami


class TestSAMIArchive:



    @pytest.fixture
    def sami_archive(self):
        ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/", "/net/aaolxz/iscsi/data/SAMI/catalogues/sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
        return ar

    @pytest.fixture
    def sami_sample(self, sami_archive):
        return sami_archive.get_full_sample()

    def test_confirm_id_data_type(self, sami_archive, sami_sample):
        assert isinstance(sami_archive.contents[0], str)
        assert isinstance(sami_sample.ids[0], str)

    # def test_get_cube_data(self, sami_archive):
    #     sami_archive.available_traits['spectral_cubes'].data_available("41144")
    #     f = sami_archive.available_traits['spectral_cubes']u'/data/SAMI/data_releases/v0.9/2015_04_14-2015_04_22/cubed/41144/41144_red_7_Y15SAR3_P002_12T085_1sec.fits.gz')
    #     f.data()

    def test_full_sample_creation(self, sami_archive):
        sami_archive.get_full_sample()

    def test_data_available(self, sami_archive):
        sami_archive.available_traits['spectral_cubes'].data_available("41144")

    def test_retrieve_data_from_sample(self, sami_sample):
        sami_sample.get_archive_id(sami_sample.get_archive_for_property(""),'41144')
        t = sami_sample['41144']['spectral_cubes', u'red.Y15SAR3_P002_12T085.1sec']
        assert isinstance(t.value, numpy.ndarray)