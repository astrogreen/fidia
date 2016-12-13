import pytest

import itertools

import numpy
from fidia.archive import sami
from fidia.traits import TraitKey, Trait, WorldCoordinateSystem
from fidia.astro_object import AstronomicalObject

@pytest.fixture(scope='module')
def sami_archive():
    # ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
    #                           "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
    #                           "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
    # ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
    #                           "/home/agreen/sami_sel_v0.9_only.fits")
    # ar = sami.SAMITeamArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
    #                           "/Users/agreen/Documents/ASVO/test_data/sami_test_release/" +
    #                           "sami_small_test_cat.fits")
    ar = sami.SAMIDR1PublicArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
                                   "dr1_catalog/dr1_20160720.txt")
    return ar

@pytest.fixture(scope='module')
def sami_sample(sami_archive):
    return sami_archive.get_full_sample()

@pytest.fixture(scope='module')
def a_sami_galaxy(sami_sample):
    return sami_sample['24433']

@pytest.fixture(scope='module')
def a_duplicate_sami_galaxy(sami_sample):
    return sami_sample['537171']

class TestSAMILZIFU:

    def test_data_available_for_duplicate_galaxy(self, a_duplicate_sami_galaxy):

        vmap = a_duplicate_sami_galaxy['velocity_map-ionized_gas']

        vmap.value.value

    def test_lzifu_velocity_map(self, sami_sample):
        vmap = sami_sample['24433']['velocity_map-ionized_gas']

        assert isinstance(vmap.value(), numpy.ndarray)

        assert vmap.shape == (1, 50, 50)

    def test_lzifu_ha_map(self, sami_sample):
        themap = sami_sample['24433']['line_emission_map', 'HALPHA']

        assert isinstance(themap.value(), numpy.ndarray)

        assert themap.shape == (50, 50)

    def test_lzifu_ha_map_multicomponent(self, sami_sample):
        themap = sami_sample['24433'][TraitKey('line_emission_map', 'HALPHA', "recom_comp")]

        assert hasattr(themap, 'comp_1_flux')
        assert hasattr(themap, 'error')

    def test_wcs_on_both_branches(self, a_sami_galaxy):

        for trait_key in a_sami_galaxy['line_emission_map-HALPHA'].get_all_branches_versions():
            trait = a_sami_galaxy[trait_key]
            wcs_sub_trait = trait['wcs']
            assert isinstance(wcs_sub_trait, WorldCoordinateSystem)


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
        a_sami_galaxy['line_emission_map', 'HALPHA'].get_sub_trait(TraitKey('wcs'))

class TestSAMISFRmaps:

    def test_sfr_map_present(self, a_sami_galaxy):

        assert isinstance(a_sami_galaxy['sfr_map'], Trait)

        assert isinstance(a_sami_galaxy['sfr_map'].value(), numpy.ndarray)

        assert isinstance(a_sami_galaxy['sfr_map'].error(), numpy.ndarray)

        assert a_sami_galaxy['sfr_map'].value().shape == a_sami_galaxy['sfr_map'].error().shape

    def test_sfr_map_present_for_duplicate_galaxy(self, a_duplicate_sami_galaxy):

        assert isinstance(a_duplicate_sami_galaxy['sfr_map'], Trait)

        assert isinstance(a_duplicate_sami_galaxy['sfr_map'].value(), numpy.ndarray)

        assert isinstance(a_duplicate_sami_galaxy['sfr_map'].error(), numpy.ndarray)

        assert a_duplicate_sami_galaxy['sfr_map'].value().shape == a_duplicate_sami_galaxy['sfr_map'].error().shape

    def test_extinction_map_present(self, a_sami_galaxy, a_duplicate_sami_galaxy):

        assert isinstance(a_sami_galaxy['extinction_map'].value(), numpy.ndarray)
        assert isinstance(a_duplicate_sami_galaxy['extinction_map'].value(), numpy.ndarray)

    def test_emission_classification_maps_present(self, a_sami_galaxy, a_duplicate_sami_galaxy):
        # type: (AstronomicalObject) -> None


        trait_list = [obj[trait] for obj, trait in itertools.product(
                          (a_sami_galaxy, a_duplicate_sami_galaxy),
                          ('emission_classification_map',
                           'emission_classification_map:1_comp',
                           'emission_classification_map:recom_comp')
                        )
                      ]

        for trait in trait_list:
            assert isinstance(trait, Trait)
            assert isinstance(trait.value(), numpy.ndarray)

            # Check that the data is in the correct range (three classes)
            assert numpy.min(trait.value()) == 0
            assert numpy.max(trait.value()) == 2