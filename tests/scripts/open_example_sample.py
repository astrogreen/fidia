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

import sys, os


if "FIDIA_TEST_DATA_DIR" in os.environ:
    TEST_DATA_DIR = os.environ["FIDIA_TEST_DATA_DIR"]
else:
    TEST_DATA_DIR = os.environ["FIDIA_TEST_DATA_DIR"] = "/tmp/fidia_test_data"

# Update the python path so that the test data generators can be found.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Import the code to generate test data
import generate_test_data as testdata

if not os.path.exists(TEST_DATA_DIR):
    # Only create the data if it doesn't already exist.
    testdata.generate_simple_dataset(TEST_DATA_DIR, 5)

from fidia.archive import example_archive

import fidia

# ar = sami.SAMITeamArchive("/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/",
#                           "/net/aaolxz/iscsi/data/SAMI/catalogues/" +
#                           "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")
# ar = sami.SAMITeamArchive("/home/agreen/sami_test_release/",
#                           "/home/agreen/sami_test_release/" +
#                           "sami_small_test_cat.fits")
# ar = sami.SAMITeamArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
#                           "/Users/agreen/Documents/ASVO/test_data/sami_test_release/sami_small_test_cat.fits")
# ar = sami.SAMIDR1PublicArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
#                                "dr1_catalog/dr1_20160720.txt")
ar = example_archive.ExampleArchive(basepath=TEST_DATA_DIR)

#sample = ar.get_full_sample()

