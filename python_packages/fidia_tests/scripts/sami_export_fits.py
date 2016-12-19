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

# sfrmap = sample['9352']['sfr_map']
#
# cube = sample['24433']['spectral_map-red']

# velmap = sample['9352']['velocity_map-ionized_gas']
#
# velmap.as_fits("9352_velmap.fits")
#
# specfit = sample['9352']['spectral_fit_cube-red']
#
# specfit.as_fits("9352_specfit.fits")

em_map = sample['24433']['line_emission_map-HALPHA']
em_map.as_fits("24433_ha_map.fits")

# ___       __    __  __
#  |   /\  |__)  / _`  /
#  |  /~~\ |  \ .\__> /_


# import fidia_tarfile_helper
#
# trait_path_list = [
#     {'sample': 'SAMI',
#      'object_id': '9352',
#      'trait_path': [
#          "velocity_map-ionized_gas"
#      ]},
#     {'sample': 'SAMI',
#      'object_id': '9352',
#      'trait_path': [
#          "velocity_dispersion_map-ionized_gas"
#      ]},
#     {'sample': 'SAMI',
#      'object_id': '24433',
#      'trait_path': [
#          "spectral_cube-blue"
#      ]}
# ]
#
# tar_stream = fidia_tarfile_helper.fidia_tar_file_generator(sample, trait_path_list)
#
# stream = fidia_tarfile_helper.Streaming(tar_stream,
#                    "example.tar.gz")
# stream.filename = "example.tar.gz"
# stream.stream()
