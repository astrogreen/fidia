import pytest

import random
import numpy
import fidia
from fidia.archive import sami

from fidia.traits.utilities import TraitKey
from fidia.traits.abstract_base_traits import AbstractBaseTrait
from fidia.exceptions import DataNotAvailable


def contains_empty_dicts(test_dict):
    for key in test_dict:
        elem = test_dict[key]
        if isinstance(elem, dict):
            if len(elem) == 0:
                return True
            else:
                return contains_empty_dicts(elem)
    return False

@pytest.fixture(scope='module')
def sami_archive():
    # ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
    #                           "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
    #                           "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
    # ar = sami.SAMITeamArchive("/home/agreen/sami_test_release/",
    #                           "/home/agreen/sami_test_release/" +
    #                           "sami_small_test_cat.fits")
    # ar = sami.SAMITeamArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
    #                           "/Users/agreen/Documents/ASVO/test_data/sami_test_release/sami_small_test_cat.fits")
    ar = sami.SAMIDR1PublicArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
                                   "dr1_catalog/dr1_20160720.txt")
    return ar

@pytest.fixture(scope='module')
def sami_sample(sami_archive):
    return sami_archive.get_full_sample()

@pytest.fixture(scope='module')
def a_sami_galaxy(sami_sample):
    return sami_sample['9352']

class TestSAMIArchive:

    def test_full_sample_creation(self, sami_archive):
        sami_archive.get_full_sample()

    def test_confirm_id_data_type(self, sami_archive, sami_sample):
        assert isinstance(next(iter(sami_archive.contents)), str)
        assert isinstance(next(iter(sami_sample.ids)), str)

    # def test_get_cube_data(self, sami_archive):
    #     sami_archive.available_traits['spectral_cubes'].data_available("41144")
    #     f = sami_archive.available_traits['spectral_cubes']u'/data/SAMI/data_releases/v0.9/2015_04_14-2015_04_22/cubed/41144/41144_red_7_Y15SAR3_P002_12T085_1sec.fits.gz')
    #     f.data()


    # def test_data_available(self, sami_archive):
    #     sami_archive.available_traits['spectral_cube'].data_available("41144")

    def test_retrieve_data_from_sample(self, sami_sample):
        sami_sample.get_archive_id(sami_sample.get_archive_for_property(TraitKey('spectral_map', 'blue')),'24433')
        # 1.0 arcsec binning
        t = sami_sample['24433']['spectral_map', 'red']
        assert isinstance(t.value(), numpy.ndarray)
        # 0.5 arcsec binning
        t = sami_sample['24433']['spectral_map', 'blue']
        assert isinstance(t.value(), numpy.ndarray)

    # This test disabled because there are no duplicates in DR1
    # def test_retrieve_data_from_sample_version_not_required(self, sami_sample):
    #     # 1.0 arcsec binning
    #     t = sami_sample['23117']['spectral_cube', 'red']
    #     assert isinstance(t.value(), numpy.ndarray)
    #     t = sami_sample['28860']['spectral_cube', 'blue']
    #     assert isinstance(t.value(), numpy.ndarray)

    # This test is disabled because currently the code has been written to
    # always return a default (as this is what is needed for SAMI). How to
    # handle defaults and multiple versions still needs to be sorted out.
    # @TODO: Defaults

    # def test_multiple_data_available(self, sami_sample):
    #     # SAMI galaxy 41144 has multiple observations on different runs.
    #     with pytest.raises(fidia.MultipleResults):
    #         sami_sample['41144']['spectral_cube', 'red.10']

    def test_attempt_retrieve_object_not_in_sample(self, sami_sample):
        with pytest.raises(fidia.NotInSample):
            sami_sample['random']['spectral_map', u'blue']

    # def test_retrieve_rss_data(self, sami_sample):
    #     t = sami_sample['41144']['rss_map', '2015_04_14-2015_04_22:15apr20015sci.fits']
    #     assert isinstance(t.value, numpy.ndarray)

    # def test_get_trait_keys_for_rss(self, sami_archive):
    #     rss_keys = sami_archive.available_traits[('rss_map')].known_keys(sami_archive)
    #     key = rss_keys.pop()
    #     sample = sami_archive.get_full_sample()
    #     assert isinstance(sample[key.object_id][key], AbstractBaseTrait)
    #
    # def test_get_all_trait_keys_archive(self, sami_archive):
    #     rss_keys = sami_archive.known_trait_keys()
    #     sample = sami_archive.get_full_sample()
    #     for key in random.sample(rss_keys, 10):
    #         try:
    #             trait = sample[key.object_id][key]
    #         except DataNotAvailable:
    #             continue
    #         else:
    #             assert isinstance(trait, AbstractBaseTrait)


class TestSAMISmartTraits:

    def test_cube_wcs(self, a_sami_galaxy):

        import astropy.wcs

        wcs = a_sami_galaxy['spectral_map', 'blue'].get_sub_trait(TraitKey('wcs'))
        assert isinstance(wcs, astropy.wcs.WCS)


    def test_cube_coord(self, a_sami_galaxy):
        import astropy.coordinates

        coord = a_sami_galaxy['spectral_map', 'blue'].get_sub_trait(TraitKey('catalog_coordinate'))
        assert isinstance(coord, astropy.coordinates.SkyCoord)


class TestSAMIArchiveSchema:

    @pytest.fixture
    def schema(self, sami_archive):
        return sami_archive.schema()

    # def test_sami_traits_have_correct_schema_structure(self, sami_archive):
    #
    #     # Iterate over all known traits for this archive:
    #     for trait_class in sami_archive.available_traits:
    #         schema = sami_archive.available_traits[trait_class].schema()
    #         # Schema should be dictionary-like:
    #         assert isinstance(schema, dict)
    #         for key in schema:
    #             # Keys should be strings
    #             assert isinstance(key, str)
    #             # Values should be strings
    #             assert isinstance(schema[key], str)
    #             # Values should be valid data-types
    #             # @TODO: Not implemented

    def test_sami_archive_schema_no_empty_elements(self, schema):

        assert not contains_empty_dicts(schema)

    def test_sami_archive_has_correct_schema_structure(self, schema, sami_archive):
        schema = sami_archive.schema()

        # Schema should be dictionary-like:
        assert isinstance(schema, dict)
        valid_trait_types = sami_archive.available_traits.get_trait_types()
        for trait_type in schema:

            # Top level of schema should be a valid trait_type:
            assert trait_type in valid_trait_types

            # Each element should be dictionary-like
            assert isinstance(schema[trait_type], dict)

            # Next level of schema should be a valid trait_qualifier or None
            valid_trait_names = sami_archive.available_traits.get_trait_names()
            for trait_qualifier in schema[trait_type]:
                assert TraitKey.as_trait_name(trait_type, trait_qualifier) in valid_trait_names

                # Each element should be dictionary-like
                assert isinstance(schema[trait_type][trait_qualifier], dict)

    def test_cube_wcs_in_schema(self, schema):
        schema['spectral_map']['red']['wcs']

class TestSAMIArchiveMetadata:

    def test_telescope_metadata(self, a_sami_galaxy):
        # type: (AstronomicalObject) -> None
        assert a_sami_galaxy['spectral_map-red'].get_sub_trait(TraitKey('telescope_metadata')).telescope() == 'Anglo-Australian Telescope'
        assert a_sami_galaxy['spectral_map-red'].get_sub_trait(TraitKey('telescope_metadata')).latitude() == -31.27704
        assert a_sami_galaxy['spectral_map-red'].get_sub_trait(TraitKey('telescope_metadata')).longitude() == 149.0661
        assert a_sami_galaxy['spectral_map-red'].get_sub_trait(TraitKey('telescope_metadata')).altitude() == 1164

    def test_short_names(self, a_sami_galaxy):
        # type: (AstronomicalObject) -> None
        tel_metadata = a_sami_galaxy['spectral_map-red'].get_sub_trait(TraitKey('telescope_metadata'))
        assert tel_metadata.telescope.get_short_name() == 'TELESCOP'
        assert tel_metadata.latitude.get_short_name() == 'LAT_OBS'

    def test_instrument_metadata(self, a_sami_galaxy):
        # type: (AstronomicalObject) -> None
        sub_trait = a_sami_galaxy['spectral_map-blue'].get_sub_trait(TraitKey('instrument_metadata'))

        assert isinstance(sub_trait, sami.SAMISpectralCube.SAMICharacteristics)

        assert sub_trait.disperser_id() == '580V'
        assert sub_trait.disperser_tilt() == 0.7
        assert sub_trait.instrument_software_date() == '17-Oct-2014'
        assert sub_trait.instrument_id() == 'AAOMEGA-SAMI'
        assert sub_trait.spectrograph_arm() == 'BL'


    def test_detector_metadata(self, a_sami_galaxy):
        # type: (AstronomicalObject) -> None
        sub_trait = a_sami_galaxy['spectral_map-blue'].get_sub_trait(TraitKey('detector_metadata'))

        assert isinstance(sub_trait, sami.SAMISpectralCube.AAOmegaDetector)

        assert sub_trait.detector_control_software_version() == 'r3_110_2_3'
        assert sub_trait.detector_id() == 'E2V2A'
