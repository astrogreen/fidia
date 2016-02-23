import numpy as np

import matplotlib.pyplot as plt

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

# Get Velocity Map for object:

vmap = s['28860']['velocity_map']



plt.imshow(vmap.data)