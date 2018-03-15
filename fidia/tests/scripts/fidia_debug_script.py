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

import re
import numpy as np

from fidia.archive import sami, example_archive
from fidia import reports

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


sample = ar.get_full_sample()



ar = sami.SAMIDR1PublicArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
	"dr1_catalog/dr1_20160720.txt")

# schema = ar.schema()

# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=tuple(), verbosity='data_only')
# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=('branch_version', ), verbosity='data_only')
# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=('branch_version', ), verbosity='metadata')
# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=tuple(), verbosity='descriptions')

# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=tuple(), verbosity='descriptions', separate_metadata=True)

# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=('no_trait_qualifier',), verbosity='descriptions')
# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=('trait_name',), verbosity='descriptions')
# schema = ar.full_schema(include_subtraits=True, data_class='all', combine_levels=('branch_version',), verbosity='simple')

# convert to nicely formatted JSON:
# json_string = json.dumps(schema, indent=4)

# print(json_string)

# t = sample['24433']['sfr_map']
# t = sample['24433']['surface_brightness']

# # schema = t.full_schema()
# schema = t.full_schema()

# specfit = sample['9352']['spectral_fit_cube-red']
#
# specfit.as_fits("9352_specfit.fits")

latex_lines = reports.content_report(ar.available_traits)

# print(schema)