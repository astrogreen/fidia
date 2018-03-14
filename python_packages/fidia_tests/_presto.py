# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

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
