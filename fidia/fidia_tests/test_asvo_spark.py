import pytest

from fidia import Sample, AstronomicalObject
from fidia.archive.asvo_spark import AsvoSparkArchive


class TestAsvoSpark:


    @pytest.fixture
    def small_canned_sample(self):
        query = u"SELECT cataid, z, metal FROM stellarmasses WHERE z < 0.05 AND z > 0.0499"
        small_canned_sample = AsvoSparkArchive().new_sample_from_query(query)
        return small_canned_sample

    def test_new_sample_from_spark(self): 
        """This test runs a canned query and confirms that the resulting
        sample has the right number of elements."""

        query = u"SELECT cataid, z, metal FROM stellarmasses WHERE z < 0.05 AND z > 0.0499"

        mysample = AsvoSparkArchive().new_sample_from_query(query)

        assert len(mysample) == 21

    # def test_spark_sample_produces_valid_xhtml(self, small_canned_sample):
    #     small_canned_sample.to_html()
