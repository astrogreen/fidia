# import json
# from collections import OrderedDict

# from typing import List, Dict

# import fidia
from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList

# from indenter import Indenter

S7_DATA_DIR = "/Users/agreen/Desktop/S7 Data"
S7_INGESTION_DIR = "/Users/agreen/Documents/ASVO/code/git-repository/ingestion/s7/"


def collect_validation_errors(output, breadcrumb=tuple()):
    result = []
    if isinstance(output, dict):
        for key, value in output.items():
            if key == 'validation_errors':
                result.append(("At " + " -> ".join(breadcrumb), value))
                # Don't process this key further:
                continue
            if isinstance(value, (dict, list)):
                result.extend(collect_validation_errors(value, breadcrumb=breadcrumb + (str(key),)))
    if isinstance(output, list):
        for key, value in enumerate(output):
            if isinstance(value, (dict, list)):
                result.extend(collect_validation_errors(value, breadcrumb=breadcrumb + ("(Item:" + str(key) + ")",)))
    return result

def format_validation_errors(errors):
    output_lines = []
    for item in errors:
        output_lines.append(item[0])
        for elem in item[1]:
            output_lines.append(4*" " + elem)
    return "\n".join(output_lines)


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

def write_specification_dict_as_json(specification_dict, json_filename):
    with open(json_filename, "w") as f:
        json.dump(specification_dict, f, indent=4)

def write_validataion_errors(specification_dict, errors_filename):
    with open(errors_filename, "w") as f:
        f.write(format_validation_errors(collect_validation_errors(specification_dict)))

def update_s7_json_from_list(list_dict):
    # type: (List[dict]) -> Dict[str, TraitMapping]

    specification_dict = dict()
    for mapping in list_dict:
        specification_dict.update(mapping)

    return specification_dict


def update_mappings_list_with_specification_dict(mappings, updated_specification_dict):
    # type: (List[TraitMapping], Dict[str, dict]) -> List
    """Update a list of TraitMapping objects using the serialised mapping information in updated_specification_dict.

    This identifies the part of the specification_dict that corresponds to each
    TraitMapping object in the list, and then calls the
    `update_with_specification_dict` method.

    """

    update_log = []

    for mapping in mappings:
        log.debug("Preparing to update %s", mapping.mapping_key_str)
        if mapping.mapping_key_str in updated_specification_dict:
            # The mapping appears in the updated information, so update mapping with that representation
            log.debug("Updated mapping information found, updating mapping...")
            log_length_before = len(update_log)
            mapping.update_with_specification_dict(updated_specification_dict[mapping.mapping_key_str], update_log=update_log)
            log_length_after = len(update_log)
            if log_length_after > log_length_before:
                log.debug("%s updates made", log_length_after - log_length_before)
                if log.isEnabledFor(slogging.VDEBUG):
                    for line in update_log[log_length_before:]:
                        log.vdebug(line)
            else:
                log.debug("No updates required.")
        else:
            # The mapping does not appear in the updated information: perhaps it has been deleted?
            log.debug("No updated mapping information found! Perhaps item has been deleted from JSON? No changes made.")

    return update_log

if __name__ == "__main__":

    all_columns_found_main = ColumnDefinitionList()
    all_dicts_main = OrderedDict()
    all_mappings_main = []

    collect_cubes(all_columns_found_main, all_dicts_main, all_mappings_main)

    collect_lzifu(all_columns_found_main, all_dicts_main, all_mappings_main)

    collect_nuclear_spectra(all_columns_found_main, all_dicts_main, all_mappings_main)

    collect_tabular_data(all_columns_found_main, all_dicts_main, all_mappings_main)

    # print(repr(all_columns_found))
    # for mapping in all_mappings:
    #     d = mapping.as_specification_dict("")
    #     print(d)
    #     print(json.dumps(d, indent=2))
    #     print("\n\n\n")
    # [print(key) for key in all_columns_found._contents.keys()]

    # print(json.dumps([mapping.as_specification_dict(all_columns_found) for mapping in all_mappings], indent=2))

    specification_dict_main = [mapping.as_specification_dict(all_columns_found_main) for mapping in all_mappings_main]


    write_specification_dict_as_json(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral.json")

    write_validataion_errors(specification_dict_main, S7_INGESTION_DIR + "s7-datacentral-error-summary.txt")


    updated_json_filename = S7_INGESTION_DIR + "s7-datacentral_ADT_20170720.json"

    with open(updated_json_filename, 'r') as f:
        updated_json = json.load(f)


    # The original S7 JSON given to Adam (the team) was written with code that
    # produced a top level list, but this was replaced with a top-level
    # dictionary (as the list provided an unnecessary level of nesting). This
    # next command changes the old format to match the new one:

    updated_json = update_s7_json_from_list(updated_json)

    # specification_dict = update_s7_json_from_list(specification_dict)

    update_log = update_mappings_list_with_specification_dict(all_mappings_main, updated_json)

    for line in update_log:
        print(line)

    # print(format_validation_errors(collect_validation_errors(specification_dict)))


    # indenter = Indenter()
    # indenter.add_line(repr(all_mappings))
    #
    # print(indenter.code)
