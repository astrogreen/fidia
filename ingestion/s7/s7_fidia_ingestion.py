from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import List, Dict

import fidia

from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList
from fidia.ingest.ingestion_helpers import *


S7_DATA_DIR = "/Users/agreen/Desktop/S7 Data/"
S7_INGESTION_DIR = "/Users/agreen/Documents/ASVO/code/git-repository/ingestion/s7/"


def collect_cubes(all_columns_found, all_dicts, all_mappings):
    # C u b e s

    cube_dicts = OrderedDict()
    cube_mappings = []

    # Blue Cubes
    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "0_Cubes/{object_id}_B.fits.gz", object_id="3C278",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    cube_dicts["FITSFile:cube_blue"] = fits_dict
    cube_mappings.append(TraitMapping(FITSFile, "cube_blue", fits_mapping))
    # cube_mappings.append(
    #     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
    #     {"FITSFile:cube_blue": fits_mapping}
    # )

    # Red Cubes
    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "0_Cubes/{object_id}_R.fits.gz", object_id="3C278",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    cube_dicts["FITSFile:cube_red"] = fits_dict
    cube_mappings.append(TraitMapping(FITSFile, "cube_red", fits_mapping))
    # cube_mappings.append(
    #     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
    #     {"FITSFile:cube_blue": fits_mapping}
    # )



    broad_cube_dict = OrderedDict()
    broad_cube_mappings = []

    # Blue Cubes
    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "0_Broadsub_cubes/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    broad_cube_dict["FITSFile:cube_blue"] = fits_dict
    broad_cube_mappings.append(TraitMapping(FITSFile, "cube_blue", fits_mapping))
    # broad_cube_mappings.append(
    #     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
    # )

    # Red Cubes
    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "0_Broadsub_cubes/{object_id}-broadsub_R.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    broad_cube_dict["FITSFile:cube_red"] = fits_dict
    broad_cube_mappings.append(TraitMapping(FITSFile, "cube_red", fits_mapping))
    # broad_cube_mappings.append(
    #     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
    #     {"FITSFile:cube_blue": fits_mapping}
    # )


    all_dicts["Group:cubes"] = {
        "Group:normal_cubes": cube_dicts,
        "Group:broad_cubes": broad_cube_dict
    }

    all_mappings.append(TraitMapping(TarFileGroup, "cubes", [
        TraitMapping(TarFileGroup, "normal_cubes", cube_mappings),
        TraitMapping(TarFileGroup, "broad_cubes", broad_cube_mappings),
    ]))


def collect_lzifu(all_columns_found, all_dicts, all_mappings):
    #   L Z I F U    G r o u p s

    lzifu_dict = OrderedDict()
    lzifu_mappings = []

    # Specific Components
    for n_comp in "1", "2", "3":
        columns_found, fits_dict, fits_mapping = finder_fits_file(
            "1_LZIFU_n_comp_fits/{object_id}_" + n_comp + "_comp.fits", object_id="ESO323-G77",
            basepath=S7_DATA_DIR
        )
        all_columns_found.extend(columns_found)
        lzifu_dict["FITSFile:comp_" + n_comp] = fits_dict
        lzifu_mappings.append(TraitMapping(FITSFile, "comp_" + n_comp, fits_mapping))

    # Best Component (LZComp)
    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "2_Post-processed_mergecomps/{object_id}_best_components.fits", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    lzifu_dict["FITSFile:best_component"] = fits_dict
    lzifu_mappings.append(TraitMapping(FITSFile, "best_component", fits_mapping))

    all_dicts["Group:lzifu"] = lzifu_dict
    all_mappings.append(TraitMapping(TarFileGroup, "lzifu", lzifu_mappings))


def collect_nuclear_spectra(all_columns_found, all_dicts, all_mappings):
    #   N u c l e a r   S p e c t r a

    nuclear_dict = OrderedDict()
    nuclear_mappings = []

    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "3_Nuclear_spectra/{object_id}_R.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_dict["FITSFile:red"] = fits_dict
    nuclear_mappings.append(TraitMapping(FITSFile, "red", fits_mapping))

    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "3_Nuclear_spectra/{object_id}_B.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_dict["FITSFile:blue"] = fits_dict
    nuclear_mappings.append(TraitMapping(FITSFile, "blue", fits_mapping))

    # Broad-line subtracted
    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "3_Broadsub_nuclear_spectra/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_dict["FITSFile:blue_broad_line_subtracted"] = fits_dict
    nuclear_mappings.append(TraitMapping(FITSFile, "blue_broad_line_subtracted", fits_mapping))

    columns_found, fits_dict, fits_mapping = finder_fits_file(
        "3_Broadsub_nuclear_spectra/{object_id}-broadsub_R.fits.gz", object_id="ESO323-G77",
        basepath=S7_DATA_DIR
    )
    all_columns_found.extend(columns_found)
    nuclear_dict["FITSFile:red_broad_line_subtracted"] = fits_dict
    nuclear_mappings.append(TraitMapping(FITSFile, "red_broad_line_subtracted", fits_mapping))

    all_dicts["Group:nuclear_spectra"] = nuclear_dict
    all_mappings.append(TraitMapping(TarFileGroup, "nuclear_spectra", nuclear_mappings))


def collect_tabular_data(all_columns_found, all_dicts, all_mappings):
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
            log.debug("Updating column '%s' with short description '%s'", column.column_name, column_meta[column.column_name]['short_description'])
            column.short_description = column_meta[column.column_name]['short_description']

    # tabular_mappings = dict()

    columns_found, table_dict, table_mapping = finder_csv_file(
        "4_Table_2_Catalogue.csv", comment="\$", index_column="S7_Name",
        basepath=S7_DATA_DIR
    )
    update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_2_Catalogue.csv")
    all_columns_found.extend(columns_found)
    all_dicts["Table:catalog"] = table_dict
    all_mappings.append(TraitMapping(Table, "catalog", table_mapping))



    columns_found, table_dict, table_mapping = finder_csv_file(
        "4_Table_3a_Nuclear_fluxes.csv", comment="\$", index_column="S7_Name",
        basepath=S7_DATA_DIR
    )
    # update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_3a_Nuclear_fluxes.csv")
    all_columns_found.extend(columns_found)
    all_dicts["Table:nuclear_fluxes"] = table_dict
    all_mappings.append(TraitMapping(Table, "nuclear_fluxes", table_mapping))

    columns_found, table_dict, table_mapping = finder_csv_file(
        "4_Table_3b_Nuclear_flux_errors.csv", comment="\$", index_column="S7_Name",
        basepath=S7_DATA_DIR
    )
    # update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_3b_Nuclear_flux_errors.csv")

    all_columns_found.extend(columns_found)
    all_dicts["Table:nuclear_flux_errors"] = table_dict
    all_mappings.append(TraitMapping(Table, "nuclear_flux_errors", table_mapping))

    columns_found, table_dict, table_mapping = finder_csv_file(
        "4_Table_4_Nuclear_luminosities.csv", comment="\$", index_column="S7_Name",
        basepath=S7_DATA_DIR
    )
    # update_s7_csv(table_mapping, columns_found, S7_DATA_DIR + "/4_Table_4_Nuclear_luminosities.csv")
    all_columns_found.extend(columns_found)
    all_dicts["Table:nuclear_luminosities"] = table_dict
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


if __name__ == "__main__":

    # Set up the variables to collect the mappings and columns:

    all_columns_found_main = ColumnDefinitionList()
    all_dicts_main = OrderedDict()
    all_mappings_main = []

    # Go through the data and auto-generate mappings and columns:

    collect_cubes(all_columns_found_main, all_dicts_main, all_mappings_main)
    collect_lzifu(all_columns_found_main, all_dicts_main, all_mappings_main)
    collect_nuclear_spectra(all_columns_found_main, all_dicts_main, all_mappings_main)
    collect_tabular_data(all_columns_found_main, all_dicts_main, all_mappings_main)

    # Display a list of columns found and mappings created:

    # print(repr(all_columns_found))
    # for mapping in all_mappings:
    #     d = mapping.as_specification_dict("")
    #     print(d)
    #     print(json.dumps(d, indent=2))
    #     print("\n\n\n")
    # [print(key) for key in all_columns_found._contents.keys()]
    # print(json.dumps([mapping.as_specification_dict(all_columns_found) for mapping in all_mappings], indent=2))

    # Combine the mappings together into a "specification_dict" and serialize that to a JSON file

    specification_dict_main = dict()
    for mapping in all_mappings_main:
        specification_dict_main.update(mapping.as_specification_dict(all_columns_found_main))
    write_specification_dict_as_json(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral.json")

    # Validate the mappings and write errors to a file:

    write_validataion_errors(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral-error-summary.txt")

    # Re-read serialised format with updates provided by Adam Thomas and apply them to our in-memory representation:

    updated_json_filename = S7_INGESTION_DIR + "s7-datacentral_ADT_20170720.json"
    # NOTE: This file was created using old code from poc/fidia/s7_ingestion.py,
    # and therefore must be updated before use here (via call to `update_s7_json_from_list` below)
    with open(updated_json_filename, 'r') as f:
        updated_json = json.load(f)
    updated_json = update_s7_json_from_list(updated_json)
    update_log = update_mappings_list_with_specification_dict(all_mappings_main, all_columns_found_main, updated_json)

    # Display a list of changes:

    for line in update_log:
        print(line)

    # Create an updated specification_dict and write out any remaining validation errors to file:

    specification_dict_main = [mapping.as_specification_dict(all_columns_found_main) for mapping in all_mappings_main]
    write_validataion_errors(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral-error-summary-updated.txt")

    # Get a list of all object_ids in S7:

    from astropy.io import ascii

    table = ascii.read(S7_DATA_DIR + "4_Table_2_Catalogue.csv", format="csv", comment="\$")
    all_object_ids = list(table["S7_Name"])

    class S7Archive(fidia.ArchiveDefinition):

        archive_id = "S7"
        archive_type = fidia.BasePathArchive

        column_definitions = all_columns_found_main

        trait_mappings = all_mappings_main

        contents = all_object_ids

        is_persisted = False

    ar = S7Archive(basepath=S7_DATA_DIR)

    print(ar['IC5063'].table['catalog'].V_app_mag)