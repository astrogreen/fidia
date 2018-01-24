"""
..
      _____ ______   _____                       _   _                _____          _
     / ____|____  | |_   _|                     | | (_)              / ____|        | |
    | (___     / /    | |  _ __   __ _  ___  ___| |_ _  ___  _ __   | |     ___   __| | ___
     \___ \   / /     | | | '_ \ / _` |/ _ \/ __| __| |/ _ \| '_ \  | |    / _ \ / _` |/ _ \
     ____) | / /     _| |_| | | | (_| |  __/\__ \ |_| | (_) | | | | | |___| (_) | (_| |  __/
    |_____/ /_/     |_____|_| |_|\__, |\___||___/\__|_|\___/|_| |_|  \_____\___/ \__,_|\___|
                                  __/ |
                                 |___/

The FIDIA S7 Ingestion Code

Filename: s7_fidia_ingestion.py


Overview
--------

This script will load S7 data as provided by Adam Thomas (ANU) into FIDIA. The
code is linear and does the following:

1. It searches through example FITS files to find all "columns" (in the FIDIA
   sense) of data, and creates a structuring that matches those original files. It
   then creates tables based on the CSV files. These are all brought together into
   a single list of Columns and a single structuring.

2. This structing and the corresponding metadata found is then written to a JSON
   file, which was sent to Adam Thomas (June 2017).

3. Adam updated the JSON to have more complete meta-data, and sent the file back
   to us, along with updated FITS files.

4. This updated JSON is read in, and used to update the original FIDIA data
   structures as generated from the original files.

5. A FIDIA `ArchiveDefinition` class is created and executed, which makes FIDIA
   aware of the new Archive.

This file is organised to first define a bunch of support functions which
basically make the actual code at the end easier to read. At the end of the file
is the actual processing wrapped in a Python "__main__" block.


About S7
--------

S7 was originally hosted on an ANU based website:

    https://miocene.anu.edu.au/S7/


Data Organisation
-----------------

The data are organised into a few broad categories with some nesting as follows:

* Spectral cubes (red and blue): stored as FITS files
* Spectral cubes with the broad component subtracted (red and blue): stored as
  FITS files, and **not present for all galaxies**.
* LZIFU Fits: stored using the standard LZIFU format, though not all lines are
  fit, so some FITS extensions are empty.
* LZIFU "best" components as determined by `LZcomp`: Similar format to LZIFU
  fits above.
* Nuclear spectra of all galaxies (red and blue): stored as FITS files.
* Broad component subtracted nuclear spectra of all galaxies (red and blue):
  stored as FITS files.
* Tabular data:
    * Catalog (CSV)
    * Nuclear fluxes (CSV)
    * Nuclear flux errors (CSV)
    * Nuclear luminosities (CSV)


"""

from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import List, Dict

import re
import os
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
# Logging configuration at end of file, before __main__ section.

S7_DATA_DIR = "/Users/agreen/Desktop/S7 Data/"
S7_INGESTION_DIR = "/Users/agreen/Documents/ASVO/code/git-repository/ingestion/s7/"
DAL_DATA_DIR = "/Users/agreen/Desktop/S7DAL/"

def collect_cubes(all_columns_found, all_mappings):
    """Find columns and structuring for S7 spectral cubes.

    This must be done for both red and blue, and for both "Regular" and "Broad"

    """

    #  R e g u l a r   C u b e s

    cube_mappings = []

    # Blue Cubes
    columns_found, fits_mapping = finder_fits_file(
        "0_Cubes/{object_id}_B.fits", object_id="3C278",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    cube_mappings.append(TraitMapping(FITSFile, "cube_blue", fits_mapping))

    # Red Cubes
    columns_found, fits_mapping = finder_fits_file(
        "0_Cubes/{object_id}_R.fits", object_id="3C278",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    cube_mappings.append(TraitMapping(FITSFile, "cube_red", fits_mapping))


    #  B r o a d   C u b e s

    broad_cube_mappings = []

    # Blue Cubes
    columns_found, fits_mapping = finder_fits_file(
        "0_Broadsub_cubes/{object_id}-broadsub_B.fits", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    broad_cube_mappings.append(TraitMapping(FITSFile, "cube_blue", fits_mapping))

    # Red Cubes
    columns_found, fits_mapping = finder_fits_file(
        "0_Broadsub_cubes/{object_id}-broadsub_R.fits", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    broad_cube_mappings.append(TraitMapping(FITSFile, "cube_red", fits_mapping))


    all_mappings.append(TraitMapping(TarFileGroup, "cubes", [
        TraitMapping(TarFileGroup, "normal_cubes", cube_mappings),
        TraitMapping(TarFileGroup, "broad_cubes", broad_cube_mappings),
    ]))


def collect_lzifu(all_columns_found, all_mappings):

    #   L Z I F U    G r o u p s

    lzifu_mappings = []

    # Specific Components
    for n_comp in "1", "2", "3":
        columns_found, fits_mapping = finder_fits_file(
            "1_LZIFU_n_comp_fits/{object_id}_" + n_comp + "_comp.fits", object_id="ESO323-G77",
            basepath=S7_DATA_DIR
        )
        all_columns_found.extend(columns_found)
        lzifu_mappings.append(TraitMapping(FITSFile, "comp_" + n_comp, fits_mapping))

    # Best Component (LZComp)
    columns_found, fits_mapping = finder_fits_file(
        "2_Post-processed_mergecomps/{object_id}_best_components.fits", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    lzifu_mappings.append(TraitMapping(FITSFile, "best_component", fits_mapping))

    all_mappings.append(TraitMapping(TarFileGroup, "lzifu", lzifu_mappings))


def collect_nuclear_spectra(all_columns_found, all_mappings):


    #   N u c l e a r   S p e c t r a

    nuclear_mappings = []

    # Red Nuclear Spectra
    columns_found, fits_mapping = finder_fits_file(
        "3_Nuclear_spectra/{object_id}_R.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_mappings.append(TraitMapping(FITSFile, "red", fits_mapping))

    # Blue Nuclear Spectra
    columns_found, fits_mapping = finder_fits_file(
        "3_Nuclear_spectra/{object_id}_B.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_mappings.append(TraitMapping(FITSFile, "blue", fits_mapping))

    # Broad-line subtracted
    columns_found, fits_mapping = finder_fits_file(
        "3_Broadsub_nuclear_spectra/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_mappings.append(TraitMapping(FITSFile, "blue_broad_line_subtracted", fits_mapping))

    columns_found, fits_mapping = finder_fits_file(
        "3_Broadsub_nuclear_spectra/{object_id}-broadsub_R.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_mappings.append(TraitMapping(FITSFile, "red_broad_line_subtracted", fits_mapping))

    all_mappings.append(TraitMapping(TarFileGroup, "nuclear_spectra", nuclear_mappings))


def collect_tabular_data(all_columns_found, all_mappings):
    #   T a b u l a r   D a t a


    # noinspection PyShadowingNames
    def update_s7_csv(table_mapping, columns, csv_file):
        with open(csv_file, 'r') as f:
            column_meta = OrderedDict()
            for line in f:
                m = re.match(r"\$ *(?P<colname>[^,]+),\"(?P<desc>[^\"]+)\",+$", line)
                if m is None:
                    continue
                column_meta[m.group('colname')] = {'short_description': m.group('desc')}

        log.debug(list(column_meta.keys()))
        for column in columns:
            log.debug("Updating column '%s' with short description '%s'",
                      column.column_name, column_meta[column.column_name]['short_description'])
            column.short_description = column_meta[column.column_name]['short_description']

    columns_found, table_mapping = finder_csv_file(
        "4_Table_2_Catalogue.csv", comment="\$", index_column="S7_Name",
        basepath=S7_DATA_DIR
    )
    update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_2_Catalogue.csv")
    all_columns_found.extend(columns_found)
    all_mappings.append(TraitMapping(Table, "catalog", table_mapping))



    columns_found, table_mapping = finder_csv_file(
        "4_Table_3a_Nuclear_fluxes.csv", comment="\$", index_column="Galaxy",
        basepath=S7_DATA_DIR
    )
    # update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_3a_Nuclear_fluxes.csv")
    all_columns_found.extend(columns_found)
    all_mappings.append(TraitMapping(Table, "nuclear_fluxes", table_mapping))

    columns_found, table_mapping = finder_csv_file(
        "4_Table_3b_Nuclear_flux_errors.csv", comment="\$", index_column="Galaxy",
        basepath=S7_DATA_DIR
    )
    # update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_3b_Nuclear_flux_errors.csv")

    all_columns_found.extend(columns_found)
    all_mappings.append(TraitMapping(Table, "nuclear_flux_errors", table_mapping))

    columns_found, table_mapping = finder_csv_file(
        "4_Table_4_Nuclear_luminosities.csv", comment="\$", index_column="Galaxy",
        basepath=S7_DATA_DIR
    )
    # update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_4_Nuclear_luminosities.csv")
    all_columns_found.extend(columns_found)
    all_mappings.append(TraitMapping(Table, "nuclear_luminosities", table_mapping))


def update_s7_json_from_list(list_dict):
    # type: (List[dict]) -> Dict[str, TraitMapping]
    """Update an old-format dictionary read from a JSON file.

    The original S7 JSON given to Adam (the team) was written with code that
    produced a top level list, but this was replaced with a top-level
    dictionary (as the list provided an unnecessary level of nesting). This
    function removes this top level list from the specification_dict

    """

    specification_dict = dict()
    for mapping in list_dict:
        specification_dict.update(mapping)

    return specification_dict


logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'poscheck': {
            'handlers': ['console'],
            'level': logging_level
        }
    }
})


#                       __        __   __
#  |\/|  /\  | |\ |    |__) |    /  \ /  ` |__/
#  |  | /~~\ | | \|    |__) |___ \__/ \__, |  \
#
# The rest of this file runs the steps of the process as described in the
# overview (at the top of the file).


if __name__ == "__main__":

    #  __  ___  ___  __      __        ___
    # /__`  |  |__  |__)    /  \ |\ | |__
    # .__/  |  |___ |       \__/ | \| |___
    # from the overview: Search for data

    # Set up the variables to collect the mappings and columns:

    all_columns_found_main = ColumnDefinitionList()
    all_mappings_main = []

    # Go through the data and auto-generate mappings and columns:

    collect_cubes(all_columns_found_main, all_mappings_main)
    collect_lzifu(all_columns_found_main, all_mappings_main)
    collect_nuclear_spectra(all_columns_found_main, all_mappings_main)
    collect_tabular_data(all_columns_found_main, all_mappings_main)

    # Display a list of columns found and mappings created:

    # print(repr(all_columns_found))
    # for mapping in all_mappings:
    #     d = mapping.as_specification_dict("")
    #     print(d)
    #     print(json.dumps(d, indent=2))
    #     print("\n\n\n")
    # [print(key) for key in all_columns_found._contents.keys()]
    # print(json.dumps([mapping.as_specification_dict(all_columns_found) for mapping in all_mappings], indent=2))

    #  __  ___  ___  __     ___       __
    # /__`  |  |__  |__)     |  |  | /  \
    # .__/  |  |___ |        |  |/\| \__/
    # from the overview: Write out to JSON

    # Combine the mappings together into a "specification_dict" and serialize that to a JSON file
    specification_dict_main = dict()
    for mapping in all_mappings_main:
        specification_dict_main.update(mapping.as_specification_dict(all_columns_found_main))
    write_specification_dict_as_json(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral.json")

    # Validate the mappings and write errors to a file:
    write_validataion_errors(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral-error-summary.txt")

    #  __  ___  ___  __      ___  __        __
    # /__`  |  |__  |__)    |__  /  \ |  | |__)
    # .__/  |  |___ |       |    \__/ \__/ |  \
    # from the overview: Read back in Adam's updated JSON

    updated_json_filename = S7_INGESTION_DIR + "s7-datacentral_ADT_20170720.json"
    # NOTE: This file was created using old code from poc/fidia/s7_ingestion.py,
    # and therefore must be updated before use here (via call to `update_s7_json_from_list` below)

    with open(updated_json_filename, 'r') as f:
        updated_json = json.load(f)

    # Update JSON from old format:
    updated_json = update_s7_json_from_list(updated_json)

    # Apply updated changes to our in-memory representation of the mapping/structuring.
    update_log = update_mappings_list_with_specification_dict(all_mappings_main, all_columns_found_main, updated_json)

    # Display a list of changes:
    for line in update_log:
        print(line)

    # Create an updated specification_dict and write out any remaining validation errors to file:
    specification_dict_main = [mapping.as_specification_dict(all_columns_found_main) for mapping in all_mappings_main]
    write_validataion_errors(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral-error-summary-updated.txt")

    #  __  ___  ___  __      ___         ___
    # /__`  |  |__  |__)    |__  | \  / |__
    # .__/  |  |___ |       |    |  \/  |___
    # from the overview: create a FIDIA `ArchiveDefinition` and load it.

    # Get a list of all object_ids in S7:
    from astropy.io import ascii
    table = ascii.read(S7_DATA_DIR + "4_Table_2_Catalogue.csv", format="csv", comment="\$")
    all_object_ids = list(table["S7_Name"])


    # Create an ArchiveDefinition for ingestion into FIDIA
    class S7Archive(fidia.ArchiveDefinition):
        archive_id = "S7"
        archive_type = fidia.BasePathArchive
        column_definitions = all_columns_found_main
        trait_mappings = all_mappings_main
        contents = all_object_ids
        is_persisted = True

    # Call the ArchiveDefinition to create a new FIDIA Archive (this also will
    # add it to FIDIA's known archives).
    print("Creating archive")
    ar = S7Archive(basepath=S7_DATA_DIR)  # type: fidia.Archive

    #  __  ___  ___  __      __
    # /__`  |  |__  |__)    /__` | \_/
    # .__/  |  |___ |       .__/ | / \
    # do a data ingestion into the data access layer.

    print("Running data ingestion")
    os.mkdir(DAL_DATA_DIR)
    file_store = fidia.dal.NumpyFileStore(DAL_DATA_DIR, use_compression=True)
    file_store.ingest_archive(ar)

    # Add this layer to FIDIA's known data access layers
    fidia.dal_host.layers.append(file_store)

    # Get a piece of data to check everything is working:
    print(ar['IC5063'].table['catalog'].V_app_mag)

