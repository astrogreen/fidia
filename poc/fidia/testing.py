import numpy as np

import fidia
from fidia.archive import sami
ar = sami.SAMITeamArchive(
    "/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/", 
    "/net/aaolxz/iscsi/data/SAMI/catalogues/" + 
    "sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits")

#ar.available_traits['spectral_cubes'].data_available("41144")

#f = ar.available_traits['spectral_cubes'](u'/data/SAMI/data_releases/v0.9/2015_04_14-2015_04_22/cubed/41144/41144_red_7_Y15SAR3_P002_12T085_1sec.fits.gz')
#f.data()

s = ar.get_full_sample()

t = s['41144']['spectral_cube', 'red.10', 'Y15SAR3_P002_12T085']

ar.available_traits['spectral_cube'].known_keys(ar)


# Ingestion stress test:

sample = ar.get_full_sample()
schema = ar.schema()

for trait_type in schema:
    for trait_key in ar.available_traits[trait_type].known_keys(ar):
        print("Working on trait: {}".format(trait_key))
        trait = sample[trait_key.object_id][trait_key]
        for data_name in schema[trait_type]:
            try:
                assert isinstance(getattr(trait, data_name), np.ndarray)
                print("+ DataAvailable and Loaded")
            except DataNotAvailable:
                print("- DataNotAvailable")
