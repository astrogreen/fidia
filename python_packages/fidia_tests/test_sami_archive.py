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

    def test_confirm_id_data_type(self, sami_archive, sami_sample):
        assert isinstance(sami_archive.contents[0], str)
        assert isinstance(sami_sample.ids[0], str)

    # def test_get_cube_data(self, sami_archive):
    #     sami_archive.available_traits['spectral_cubes'].data_available("41144")
    #     f = sami_archive.available_traits['spectral_cubes']u'/data/SAMI/data_releases/v0.9/2015_04_14-2015_04_22/cubed/41144/41144_red_7_Y15SAR3_P002_12T085_1sec.fits.gz')
    #     f.data()

    def test_full_sample_creation(self, sami_archive):
        sami_archive.get_full_sample()

    # def test_data_available(self, sami_archive):
    #     sami_archive.available_traits['spectral_cube'].data_available("41144")

    def test_retrieve_data_from_sample(self, sami_sample):
        sami_sample.get_archive_id(sami_sample.get_archive_for_property('spectral_cube'),'41144')
        # 1.0 arcsec binning
        t = sami_sample['41144']['spectral_cube', 'red.10', 'Y15SAR3_P002_12T085']
        assert isinstance(t.value, numpy.ndarray)
        # 0.5 arcsec binning
        t = sami_sample['41144']['spectral_cube', 'red.05', 'Y15SAR3_P002_12T085']
        assert isinstance(t.value, numpy.ndarray)

    def test_retrieve_data_from_sample_version_not_required(self, sami_sample):
        # 1.0 arcsec binning
        t = sami_sample['23117']['spectral_cube', 'red.10']
        assert isinstance(t.value, numpy.ndarray)
        t = sami_sample['23117']['spectral_cube', 'red.05']
        assert isinstance(t.value, numpy.ndarray)
        t = sami_sample['23117']['spectral_cube', 'blue.05']
        assert isinstance(t.value, numpy.ndarray)
        t = sami_sample['23117']['spectral_cube', 'blue.10']
        assert isinstance(t.value, numpy.ndarray)

    def test_multiple_data_available(self, sami_sample):
        # SAMI galaxy 41144 has multiple observations on different runs.
        with pytest.raises(fidia.MultipleResults):
            sami_sample['41144']['spectral_cube', 'red.10']

    def test_attempt_retrieve_data_not_available(self, sami_sample):
        sami_sample.get_archive_id(sami_sample.get_archive_for_property('spectral_cube'),'41144')
        with pytest.raises(fidia.DataNotAvailable):
            sami_sample['41144']['spectral_cube', u'red.garbage', 'Y15SAR3_P002_12T085']

    def test_attempt_retrieve_object_not_in_sample(self, sami_sample):
        with pytest.raises(fidia.NotInSample):
            sami_sample['random']['spectral_cube', u'red.garbage', 'Y15SAR3_P002_12T085']

    def test_retrieve_rss_data(self, sami_sample):
        t = sami_sample['41144']['rss_map', '2015_04_14-2015_04_22:15apr20015sci.fits']
        assert isinstance(t.value, numpy.ndarray)

    def test_sami_traits_have_correct_schema_structure(self, sami_archive):

        # Iterate over all known traits for this archive:
        for trait_class in sami_archive.available_traits:
            schema = sami_archive.available_traits[trait_class].schema()
            # Schema should be dictionary-like:
            assert isinstance(schema, dict)
            for key in schema:
                # Keys should be strings
                assert isinstance(key, str)
                # Values should be strings
                assert isinstance(schema[key], str)
                # Values should be valid data-types
                # @TODO: Not implemented

    def test_sami_archive_has_correct_schema_structure(self, sami_archive):
        schema = sami_archive.schema()

        # Schema should be dictionary-like:
        assert isinstance(schema, dict)
        for trait_type in schema:

            # Top level of schema should be a valid trait_type:
            assert trait_type in map(lambda tk: tk.trait_type, sami_archive.available_traits)

            # Each element should be dictionary-like
            assert isinstance(schema[trait_type], dict)

    def test_get_trait_keys_for_rss(self, sami_archive):
        rss_keys = sami_archive.available_traits[('rss_map')].known_keys(sami_archive)
        key = rss_keys.pop()
        sample = sami_archive.get_full_sample()
        assert isinstance(sample[key.object_id][key], AbstractBaseTrait)

    def test_get_all_trait_keys_archive(self, sami_archive):
        rss_keys = sami_archive.known_trait_keys()
        sample = sami_archive.get_full_sample()
        for key in random.sample(rss_keys, 10):
            assert isinstance(sample[key.object_id][key], AbstractBaseTrait)