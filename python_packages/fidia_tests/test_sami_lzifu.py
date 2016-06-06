import pytest

import numpy
from fidia.archive import sami
from fidia.traits import TraitKey

class TestSAMILZIFU:

    @pytest.fixture
    def sami_archive(self):
        # ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
        #                           "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
        #                           "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
        ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
                                  "/home/agreen/sami_sel_v0.9_only.fits")
        return ar

    @pytest.fixture
    def sami_sample(self, sami_archive):
        return sami_archive.get_full_sample()



    def test_lzifu_velocity_map(self, sami_sample):
        vmap = sami_sample['28860']['velocity_map']

        assert isinstance(vmap.value(), numpy.ndarray)

        assert vmap.shape == (50, 50)

    def test_lzifu_ha_map(self, sami_sample):
        themap = sami_sample['28860']['line_map', 'HALPHA']

        assert isinstance(themap.value(), numpy.ndarray)

        assert themap.shape == (50, 50)

    def test_lzifu_ha_map_multicomponent(self, sami_sample):
        themap = sami_sample['28860']['line_map', 'HALPHA']

        assert hasattr(themap, 'comp_1_flux')
        assert hasattr(themap, 'variance')

        # theoldmap = sami_sample['28860'][TraitKey('line_map', 'HALPHA', branch='1_comp', version='0.9')]
        #
        # assert not hasattr(themap, 'comp_1_flux')

        # theoldmap = sami_sample['28860'][TraitKey('line_map', 'HALPHA', branch='recommended', version='0.9')]
        #
        # assert not hasattr(themap, 'comp_1_flux')

    def test_lzifu_continuum_cube(self, sami_sample):
        themap = sami_sample['28860']['spectral_continuum_cube', 'red']

        assert isinstance(themap.value(), numpy.ndarray)

        assert themap.shape == (2048, 50, 50)

    def test_lzifu_line_cube(self, sami_sample):
        themap = sami_sample['28860']['spectral_line_cube', 'blue']

        assert isinstance(themap.value(), numpy.ndarray)

        assert themap.shape == (2048, 50, 50)
