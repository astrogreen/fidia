
from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import List, Dict

import re
import os
import json
from collections import OrderedDict

from astropy.io import fits

import fidia

from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList
from fidia.ingest.ingestion_helpers import *
from fidia.traits import *

import logging.config
log = logging.getLogger(__name__)
logging_level = logging.WARNING
# Logging configuration at end of file, before __main__ section.

GALAH_DATA_DIR = "/Users/agreen/Research/galah/data/iDR2"
S7_INGESTION_DIR = "/Users/agreen/Documents/ASVO/code/git-repository/ingestion/s7/"
DAL_DATA_DIR = "/Users/agreen/Desktop/S7DAL/"

def fits_binary_table_data_finder(fits_file):
    pass


class GALAH_iDR2(fidia.ArchiveDefinition):

    archive_id = "GALAH_iDR2"
    archive_type = fidia.BasePathArchive
    is_persisted = True

    def __init__(self, basepath=None):

        # Find all Cannon columns

        self.column_definitions = []

        # Check that the necessary table files exist:
        assert os.path.exists(os.path.join(basepath, "sobject_iraf_iDR2_171103_cannon.fits")), \
            os.path.join(basepath, "sobject_iraf_iDR2_171103_cannon.fits") + " is missing."
        assert os.path.exists(os.path.join(basepath, "sobject_iraf_iDR2_171103_sme.fits"))


        with fits.open(os.path.join(basepath, "sobject_iraf_iDR2_171103_cannon.fits")) as hdu_list:
            tab = hdu_list[1]

            column_names = [c.name for c in tab.columns]

            for idx, name in enumerate(column_names):

                coldef = fidia.FITSBinaryTableColumn(
                    "sobject_iraf_iDR2_171103_cannon.fits",
                    1,
                    name,
                    "galah_id")

                try:
                    coldef.short_description = tab.header["TCOMM" + str(idx+1)]
                except KeyError:
                    pass

                if name == "ra" or name == "dec":
                    coldef.unit = "degree"

                aliased_coldef = (name, coldef)

                self.column_definitions.append(aliased_coldef)

            # Find element names with abundances:
            abundance_elements = []
            abundance_mappings = []
            for name in column_names:
                match = re.match(r"^([A-Za-z]+)_abund_cannon$", name)
                if match:
                    element_name = match.group(1)
                    abundance_elements.append(element_name)

                    # Create the corresponding trait mapping:
                    tm = TraitMapping(CannonAbundance, element_name, [
                        TraitPropertyMapping('value', "{}_abund_cannon".format(element_name)),
                        TraitPropertyMapping('error', "e_{}_abund_cannon".format(element_name)),
                        TraitPropertyMapping('flag', "flag_{}_abund_cannon".format(element_name)),
                        TraitPropertyMapping('norm_depth', "ld_{}_abund_cannon".format(element_name)),
                        TraitPropertyMapping('depth', "ld_{}_abund_cannon".format(element_name)),
                        TraitPropertyMapping('sn', "sn_{}_abund_cannon".format(element_name)),
                        TraitPropertyMapping('chi2', "chi2_{}_abund_cannon".format(element_name))
                    ])
                    abundance_mappings.append(tm)

            # All Object IDs
            self.contents = [str(i) for i in tab.data["galah_id"]]


        cannon_trait_properties = [
            TraitPropertyMapping('chi2', "chi2_cannon"),
            TraitPropertyMapping('flag', "flag_cannon"),
            TraitPropertyMapping('reduction_flag', "red_flag")
        ]

        # Basic Stellar Properties
        stellar_properties = [
            TraitMapping(EffectiveTemperature, "GUESS", [
                TraitPropertyMapping('value', "teff_guess")
            ]),
            TraitMapping(EffectiveTemperature, "Cannon", [
                TraitPropertyMapping('value', "Teff_cannon"),
                TraitPropertyMapping('error', "e_Teff_cannon")
            ]),
            TraitMapping(LogGravity, "GUESS", [
                TraitPropertyMapping('value', "logg_guess")
            ]),
            TraitMapping(LogGravity, "Cannon", [
                TraitPropertyMapping('value', "Logg_cannon"),
                TraitPropertyMapping('error', "e_Logg_cannon")
            ]),
            TraitMapping(Metallicity, "GUESS", [
                TraitPropertyMapping('value', "feh_guess")
            ]),
            TraitMapping(Metallicity, "Cannon", [
                TraitPropertyMapping('value', "Feh_cannon"),
                TraitPropertyMapping('error', "e_Feh_cannon")
            ])

        ]

        # stellar_properties = TraitMapping(DMU,)

        self.trait_mappings = [
            TraitMapping(DMU, "TheCannon", abundance_mappings + cannon_trait_properties + stellar_properties),
            TraitMapping(SkyCoordinate, "galah", [
                TraitPropertyMapping('ra', "ra"),
                TraitPropertyMapping('dec', "dec")
            ])
        ]


if __name__ == "__main__":

    ar = GALAH_iDR2(basepath="/Users/agreen/Research/galah/data/iDR2/")

    a_gid = ar.contents[0]

    dmu = ar[a_gid].dmu["TheCannon"]

    trait = dmu.cannon_abundance["Mo"]

