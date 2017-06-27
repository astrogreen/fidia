import json
from collections import OrderedDict

import fidia
from fidia.ingest.data_finder import *
from indenter import Indenter

dict = OrderedDict

all_columns_found = []
all_dicts = dict()
all_mappings = []

# C u b e s

cube_dicts = dict()
cube_mappings = []

# Blue Cubes
columns_found, fits_dict, fits_mapping = finder_fits_file(
    "0_Cubes/{object_id}_B.fits.gz", object_id="3C278",
    basepath="/Users/agreen/Desktop/S7 Data"
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
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
cube_dicts["FITSFile:cube_red"] = fits_dict
cube_mappings.append(TraitMapping(FITSFile, "cube_red", fits_mapping))
# cube_mappings.append(
#     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
#     {"FITSFile:cube_blue": fits_mapping}
# )



broad_cube_dict = dict()
broad_cube_mappings = []

# Blue Cubes
columns_found, fits_dict, fits_mapping = finder_fits_file(
    "0_Broadsub_cubes/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
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
    basepath="/Users/agreen/Desktop/S7 Data"
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

#   L Z I F U    G r o u p s

lzifu_mappings = dict()

# Specific Components
for n_comp in "1", "2", "3":
    columns_found, fits_mapping = finder_fits_file(
        "1_LZIFU_n_comp_fits/{object_id}_" + n_comp + "_comp.fits", object_id="ESO323-G77",
        basepath="/Users/agreen/Desktop/S7 Data"
    )
    all_columns_found.extend(columns_found)
    lzifu_mappings["FITSFile:" + n_comp +"_component"] = fits_mapping


# Best Component (LZComp)
columns_found, fits_mapping = finder_fits_file(
    "2_Post-processed_mergecomps/{object_id}_best_components.fits", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
lzifu_mappings["FITSFile:best_component"] = fits_mapping

all_mappings["Group:lzifu"] = lzifu_mappings


#   N u c l e a r   S p e c t r a

nuclear_mappings = dict()

columns_found, fits_mapping = finder_fits_file(
    "3_Nuclear_spectra/{object_id}_R.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
nuclear_mappings["FITSFile:red"] = fits_mapping

columns_found, fits_mapping = finder_fits_file(
    "3_Nuclear_spectra/{object_id}_B.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
nuclear_mappings["FITSFile:blue"] = fits_mapping

# Broad-line subtracted
columns_found, fits_mapping = finder_fits_file(
    "3_Broadsub_nuclear_spectra/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
nuclear_mappings["FITSFile:red_broad_line_subtracted"] = fits_mapping

columns_found, fits_mapping = finder_fits_file(
    "3_Broadsub_nuclear_spectra/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
nuclear_mappings["FITSFile:blue_broad_line_subtracted"] = fits_mapping

all_mappings["Group:nuclear_spectra"] = nuclear_mappings


#   T a b u l a r   D a t a

# tabular_mappings = dict()

columns_found, table_mapping = finder_csv_file(
    "4_Table_2_Catalogue.csv", comment="\$", index_column="S7_Name",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_mappings["Table:catalog"] = table_mapping

columns_found, table_mapping = finder_csv_file(
    "4_Table_3a_Nuclear_fluxes.csv", comment="\$", index_column="S7_Name",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_mappings["Table:nuclear_fluxes"] = table_mapping

columns_found, table_mapping = finder_csv_file(
    "4_Table_3b_Nuclear_flux_errors.csv", comment="\$", index_column="S7_Name",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_mappings["Table:nuclear_flux_errors"] = table_mapping

columns_found, table_mapping = finder_csv_file(
    "4_Table_4_Nuclear_luminosities.csv", comment="\$", index_column="S7_Name",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_mappings["Table:nuclear_luminosities"] = table_mapping



# print(repr(all_columns_found))
# for mapping in all_mappings:
#     d = mapping.as_specification_dict("")
#     print(d)
#     print(json.dumps(d, indent=2))
#     print("\n\n\n")
print(json.dumps([mapping.as_specification_dict("") for mapping in all_mappings], indent=2))

with open("/Users/agreen/Desktop/s7-datacentral.json", "w") as f:
    json.dump(
        [mapping.as_specification_dict("") for mapping in all_mappings],
        f)

# indenter = Indenter()
# indenter.add_line(repr(all_mappings))
#
# print(indenter.code)