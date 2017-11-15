from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import List, Dict

import re
import json
from collections import OrderedDict

import fidia

from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList
from fidia.ingest.ingestion_helpers import *
from fidia.traits import *

import logging.config
log = logging.getLogger(__name__)
logging_level = logging.WARNING


SAMI_DATA_DIR = "/Users/agreen/Documents/ASVO/test_data/sami_test_release/v0.9"


def collect_cubes(all_columns_found, all_mappings):

    cube_mappings = []

    # Blue Cubes
    columns_found, fits_mapping = finder_fits_file(
        "data_releases/v0.9/2015_01_19-2015_01_26/cubed/{object_id}/{object_id}_red_8_Y14SAR3_P005_12T056.fits.gz",
        object_id="100175",
        basepath=SAMI_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    all_mappings.append(TraitMapping(FITSFile, "cube_blue", fits_mapping))


if __name__ == "__main__":

    all_columns_found_main = ColumnDefinitionList()
    all_mappings_main = []

    # Explore/find SAMI Cubes

    collect_cubes(all_columns_found_main, all_mappings_main)

    class SAMIDR1(fidia.ArchiveDefinition):
        archive_id = "SAMI_DR1"
        archive_type = fidia.BasePathArchive
        column_definitions = all_columns_found_main
        trait_mappings = all_mappings_main
        contents = ["100175"]
        is_persisted = False


    ar = SAMIDR1(basepath=SAMI_DATA_DIR)



