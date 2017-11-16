from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import List, Dict

import os
from glob import glob
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


def create_symlinked_cubes(team_format_data_dir, catalog_file, cube_symlink_dir):
    """Go through the SAMI catalog file and create a directory full of symlinks to cubes using sensible names.

    The SAMI Team directory format is something like:

        data_releases/v0.9/2015_01_19-2015_01_26/cubed/100175/100175_blue_8_Y14SAR3_P005_12T056.fits.gz

    However, things like the observing run dates, plate ID, number of RSS files
    included in combination, etc, are difficult to reconstruct when ingesting data into FIDIA.

    This script goes through the catalog file (which has two columns: ID, and
    the full name of the red cube file) and constructs a series of simply named
    symlinks to those files.


    Parameters
    ----------
    team_format_data_dir: str
        full path to the base of the team formatted directory (e.g.
        /Users/agreen/Documents/ASVO/test_data/sami_test_release/v0.9)
    catalog_file: str
        path to the SAMI catalog file
    cube_symlink_dir: str
        full path to the directory for the symlinks to be created in


    Returns
    -------
    symlinks_created: int
        total number of symlinks created (which could be used as a sanity check)


    Notes
    -----
    The catalog file must list filenames with the ".gz" extension, regardless of
    whether the files in the team structure have that extension or not.


    """

    # Find all cube files in the team_format_directory
    # file_map = dict()
    # for dirpath, dirnames, filenames in os.walk(team_format_data_dir, topdown=True):
    #
    #     # Filter out the non-cube directories from the walk
    #     if "cubed" in dirnames:
    #         dirnames.pop("raw")
    #         dirnames.pop("reduced")
    #     for filename in filenames:
    #         if filename.encode(".fits") or filename.endswith(".fits.gz"):
    #             assert filename not in file_map, \
    #                 "Duplicate filename %s found in %s and %s" % (filename, file_map[filename], dirpath)
    #             file_map[filename] =

    def create_sym_link(team_path, object_id, color):
        extension = "fits.gz" if team_path.endswith("fits.gz") else "fits"
        link_name = os.path.join(
            cube_symlink_dir,
            "{object_id}-{color}.{extension}".format(object_id=object_id, extension=extension, color=color))
        os.symlink(team_path, link_name)
        log.info("Symlink created, %s -> %s", team_path, link_name)

    sym_links_created = 0

    with open(catalog_file, "r") as fh:
        for line in fh.readlines():
            object_id, red_fits_filename = line.split()  # type: str, str
            object_id = object_id.strip()
            red_fits_filename = red_fits_filename.strip()
            blue_fits_filename = red_fits_filename.replace("red", "blue")

            available_cube_files = glob(team_format_data_dir + "/*/cubed/{object_id}/*".format(object_id=object_id))

            for team_path in available_cube_files:
                if team_path.endswith(red_fits_filename) or (team_path + ".gz").endswith(red_fits_filename):
                    # Found the red cube. Make the symlink
                    create_sym_link(team_path, object_id, "red")
                    sym_links_created += 1
                if team_path.endswith(blue_fits_filename) or (team_path + ".gz").endswith(blue_fits_filename):
                    # Found the blue cube. Make the symlink
                    create_sym_link(team_path, object_id, "blue")
                    sym_links_created += 1

    return sym_links_created

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

    symlink_dir = os.path.join(SAMI_DATA_DIR, "data_releases", "dr1_symlinks")
    # If necessary, create the symlink directory and symlinks to cubes.
    if not os.path.exists(symlink_dir):
        os.mkdir(symlink_dir)
        create_symlinked_cubes(os.path.join(SAMI_DATA_DIR, "data_releases", "v0.9"),
                               os.path.join(SAMI_DATA_DIR, "catalogues", "dr1_catalog", "dr1_test_sample.txt"),
                               symlink_dir)


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
