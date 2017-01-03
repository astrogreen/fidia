import json

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
# ar = example_archive.ExampleArchive()

ar = sami.SAMIDR1PublicArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
                               "dr1_catalog/dr1_20160720.txt")

latex_lines = reports.content_report(ar.available_traits)

for line in latex_lines:
    print(line)

output = "\n".join(latex_lines)

print(output)

# Also write it to a file on the desktop...
with open('/Users/agreen/Documents/ASVO/meetings/sami_team/data-structure/traits.tex', 'w') as f:
    f.write(output)

reports.schema_hierarchy(ar.available_traits)
