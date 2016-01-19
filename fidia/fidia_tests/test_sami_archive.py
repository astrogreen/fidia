import pytest

import numpy

import fidia
from fidia.archive import sami

from fidia.traits.utilities import TraitKey

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
        sami_sample.get_archive_id(sami_sample.get_archive_for_property(""),'41144')
        # 1.0 arcsec binning
        t = sami_sample['41144']['spectral_cube', 'red.1sec', 'Y15SAR3_P002_12T085']
        assert isinstance(t.value, numpy.ndarray)
        # 0.5 arcsec binning
        t = sami_sample['41144']['spectral_cube', 'red.', 'Y15SAR3_P002_12T085']
        assert isinstance(t.value, numpy.ndarray)

    def test_attempt_retrieve_data_not_available(self, sami_sample):
        sami_sample.get_archive_id(sami_sample.get_archive_for_property(""),'41144')
        with pytest.raises(fidia.DataNotAvailable):
            sami_sample['41144']['spectral_cube', u'red.garbage', 'Y15SAR3_P002_12T085']

    def test_attempt_retrieve_object_not_in_sample(self, sami_sample):
        with pytest.raises(fidia.NotInSample):
            sami_sample['random']['spectral_cube', u'red.garbage', 'Y15SAR3_P002_12T085']

    def test_retrieve_rss_data(self, sami_sample):
        t = sami_sample['41144']['rss_map', '2015_04_14-2015_04_22:15apr20015sci.fits']
        assert isinstance(t.value, numpy.ndarray)

    def test_sami_traits_have_correct_schema(self, sami_archive):
        rss_trait = sami_archive.available_traits[TraitKey('rss_map')]
        schema = rss_trait.schema()
        #schema.sort()
        #assert schema == ['value', 'variance']
        assert schema == {'value': 'float.array', 'variance': 'float.array'}