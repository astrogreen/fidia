import re
import numpy as np

from fidia.archive import sami, example_archive


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

specfit = sample['9352']['spectral_fit_cube-red']

specfit.as_fits("9352_specfit.fits")

# print(schema)