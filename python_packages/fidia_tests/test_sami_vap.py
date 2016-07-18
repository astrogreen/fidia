import pytest

import numpy
from fidia.archive import sami
from fidia.traits import TraitKey, Trait

@pytest.fixture(scope='module')
def sami_archive():
    # ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
    #                           "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
    #                           "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
    # ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
    #                           "/home/agreen/sami_sel_v0.9_only.fits")
    ar = sami.SAMITeamArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
                              "/Users/agreen/Documents/ASVO/test_data/sami_test_release/" +
                              "sami_small_test_cat.fits")
    return ar

@pytest.fixture(scope='module')
def sami_sample(sami_archive):
    return sami_archive.get_full_sample()

@pytest.fixture(scope='module')
def a_sami_galaxy(sami_sample):
    return sami_sample['24433']

class TestSAMILZIFU:

    def test_lzifu_velocity_map(self, sami_sample):
        vmap = sami_sample['24433']['velocity_map']

        assert isinstance(vmap.value(), numpy.ndarray)

        assert vmap.shape == (50, 50)

    def test_lzifu_ha_map(self, sami_sample):
        themap = sami_sample['24433']['line_map', 'HALPHA']

        assert isinstance(themap.value(), numpy.ndarray)

        assert themap.shape == (50, 50)

    def test_lzifu_ha_map_multicomponent(self, sami_sample):
        themap = sami_sample['24433'][TraitKey('line_map', 'HALPHA', "recom_comp")]

        assert hasattr(themap, 'comp_1_flux')
        assert hasattr(themap, 'variance')

        # theoldmap = sami_sample['28860'][TraitKey('line_map', 'HALPHA', branch='1_comp', version='0.9')]
        #
        # assert not hasattr(themap, 'comp_1_flux')

        # theoldmap = sami_sample['28860'][TraitKey('line_map', 'HALPHA', branch='recommended', version='0.9')]
        #
        # assert not hasattr(themap, 'comp_1_flux')

    # Tests below disabled because the SAMI data does not currently include these data.
    # (AWG, 2016-06-23)

    # def test_lzifu_continuum_cube(self, sami_sample):
    #     themap = sami_sample['24433']['spectral_continuum_cube', 'red']
    #
    #     assert isinstance(themap.value(), numpy.ndarray)
    #
    #     assert themap.shape == (2048, 50, 50)
    #
    # def test_lzifu_line_cube(self, sami_sample):
    #     themap = sami_sample['24433']['spectral_line_cube', 'blue']
    #
    #     assert isinstance(themap.value(), numpy.ndarray)
    #
    #     assert themap.shape == (2048, 50, 50)

    def test_lzifu_wcs(self, a_sami_galaxy):
        a_sami_galaxy['line_map', 'HALPHA'].get_sub_trait(TraitKey('wcs'))

class TestSAMISFRmaps:

    def test_sfr_map_present(self, a_sami_galaxy):

        assert isinstance(a_sami_galaxy['sfr_map'], Trait)

        assert isinstance(a_sami_galaxy['sfr_map'].value(), numpy.ndarray)

        assert isinstance(a_sami_galaxy['sfr_map'].variance(), numpy.ndarray)

        assert a_sami_galaxy['sfr_map'].value().shape == a_sami_galaxy['sfr_map'].variance().shape



    def test_extinction_map_present(self, a_sami_galaxy):
        assert isinstance(a_sami_galaxy['extinction_map'], Trait)