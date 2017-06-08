import re
import numpy as np

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
ar = example_archive.ExampleArchive(basepath="/tmp")

#sample = ar.get_full_sample()

