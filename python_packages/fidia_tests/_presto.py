from fidia.archive.presto import PrestoArchive

class TestPresto():

    # def test_get_tablenames(self):
    #     r = PrestoArchive().get_tablenames()
    #     assert isinstance(r, list)
    #
    # def test_get_columnnames(self):
    #     r = PrestoArchive().get_columnnames('InputCatA')
    #     assert isinstance(r, list)
    #
    # def test_execute_query(self):
    #     r = PrestoArchive().execute_query('')
    #     print(r.status_code, r.reason)
    #
    #     print(r.text)

    def test_get_sql_schema(self):
        r = PrestoArchive().get_sql_schema()
        assert isinstance(r, list)

    # def test_get_dmus(self):
    #     r = PrestoArchive().get_dmu_data()
    #     assert isinstance(r, list)
    #
    # def test_get_tables_by_dmu(self):
    #     r = PrestoArchive().get_tables_by_dmu(32)
    #     assert isinstance(r, list)
    #
    # def test_get_columns_by_table(self):
    #     r = PrestoArchive().get_columns_by_table(4)
    #     assert isinstance(r, list)

    # def test_getSpectralMapTraitPropertyById(self):
    #     r = PrestoArchive().getSpectralMapTraitPropertyById('covariance', '31509')
    #     assert r is not None
