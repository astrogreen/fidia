from fidia.archive.presto import PrestoArchive

class TestPresto():

    # def test_get_tablenames(self):
    #     r = PrestoArchive().get_tablenames()
    #     assert isinstance(r, list)
    #
    # def test_get_columnnames(self):
    #     r = PrestoArchive().get_columnnames('sami_spectral_maps')
    #     assert isinstance(r, list)
    #
    # def test_execute_query(self):
    #     r = PrestoArchive().execute_query('')
    #     print(r.status_code, r.reason)
    #
    #     print(r.text)

    def test_getSpectralMapTraitPropertyById(self):
        r = PrestoArchive().getSpectralMapTraitPropertyById('covariance', '31509')
        assert r is not None
