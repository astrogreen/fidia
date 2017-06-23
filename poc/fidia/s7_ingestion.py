import json

import fidia
from fidia.ingest.data_finder import *


all_columns_found = []
all_mappings = dict()

# C u b e s

cube_mappings = dict()

# Blue Cubes
columns_found, fits_mapping = finder_fits_file(
    "0_Cubes/{object_id}_B.fits.gz", object_id="3C278",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
cube_mappings["FITSFile:cube_blue"] = fits_mapping
# cube_mappings.append(
#     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
#     {"FITSFile:cube_blue": fits_mapping}
# )

# Red Cubes
columns_found, fits_mapping = finder_fits_file(
    "0_Cubes/{object_id}_B.fits.gz", object_id="3C278",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
cube_mappings["FITSFile:cube_blue"] = fits_mapping
# cube_mappings.append(
#     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
#     {"FITSFile:cube_blue": fits_mapping}
# )

broad_cube_mappings = dict()

# Blue Cubes
columns_found, fits_mapping = finder_fits_file(
    "0_Broadsub_cubes/{object_id}-broadsub_B.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
broad_cube_mappings["FITSFile:cube_blue"] = fits_mapping
# broad_cube_mappings.append(
#     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
# )

# Red Cubes
columns_found, fits_mapping = finder_fits_file(
    "0_Broadsub_cubes/{object_id}-broadsub_R.fits.gz", object_id="ESO323-G77",
    basepath="/Users/agreen/Desktop/S7 Data"
)
all_columns_found.extend(columns_found)
broad_cube_mappings["FITSFile:cube_blue"] = fits_mapping
# broad_cube_mappings.append(
#     # TraitMapping(FITSFile, "cube_blue", fits_mapping)
#     {"FITSFile:cube_blue": fits_mapping}
# )


all_mappings["TarFileGroup:cubes"] = {
    "TarFileGroup:normal_cubes": cube_mappings,
    "TarFileGroup:broad_cubes": broad_cube_mappings
}

# print(repr(all_columns_found))
# print(json.dumps(all_mappings, indent=2))

with open("/Users/agreen/Desktop/s7-datacentral.json", "w") as f:
    json.dump(all_mappings, f)