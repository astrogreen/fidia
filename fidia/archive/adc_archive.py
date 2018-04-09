# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Iterable, Type, Any
import fidia

# Python Standard Library Imports
import json
import os
pjoin = os.path.join

# Other Library Imports
import pandas as pd

# FIDIA Imports
from . import ArchiveDefinition


# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['DataCentralArchive']


def meta_data_loader(path, archive_id, metadata_name):

    metadata_filename = pjoin(path, archive_id + "_" + metadata_name + ".csv")
    assert os.path.exists(metadata_filename), \
        "%s file missing: %s" % (metadata_name, metadata_filename)

    return pd.read_csv(metadata_filename, delimiter="|", index_col="name")

class DataCentralArchive(ArchiveDefinition):

    archive_id = "S7"
    archive_type = fidia.BasePathArchive
    # column_definitions = all_columns_found_main
    # trait_mappings = all_mappings_main
    # contents = None
    is_persisted = False

    def __init__(self, **kwargs):
        super(DataCentralArchive, self).__init__(**kwargs)

        basepath = kwargs["basepath"]  # type: str

        # Toplevel directory of the archive is named with the survey name
        survey_name = os.path.split(basepath)[1]

        data_releases = [subdir for subdir in os.listdir(basepath) if os.path.isdir(pjoin(basepath, subdir))]

        # Currently, we only support one data_release in this directory.
        assert len(data_releases) == 1, "There can be only one data_release (subdir) in the survey directory."
        data_release = data_releases[0]

        self.archive_id = survey_name + "_" + data_release

        # Find catalog data
        group_metadata_filename = pjoin(basepath, data_release, self.archive_id + "_group_meta.csv")
        if os.path.exists(group_metadata_filename):
            # Catalog information exists. Load it.

            catalog_columns = []  # type: List[fidia.ColumnDefinition]
            catalog_mappings = []  # type: List[fidia.traits.TraitMapping]

            group_meta = pd.read_csv(group_metadata_filename, delimiter="|", index_col="name")

            # Load primary key information
            primary_key_metadata = meta_data_loader(pjoin(basepath, data_release), self.archive_id, "primary_key_meta")

            for group_name in group_meta.index:

                group_dir = pjoin(basepath, data_release, group_name)
                assert os.path.exists(group_dir) and os.path.isdir(group_dir), \
                    "Group directory missing for catalog group %s" % group_name

                table_metadata = meta_data_loader(group_dir, self.archive_id,  "table_meta")

                group_tables = []  # type: List[fidia.traits.TraitMapping]

                for table_name in table_metadata.index:
                    table_dir = pjoin(group_dir, table_name)
                    assert os.path.exists(table_dir) and os.path.isdir(table_dir), \
                        "Table directory is missing for table %s" % table_name

                    column_metadata = meta_data_loader(table_dir, self.archive_id, "column_meta")

                    key_column = table_metadata.get_value(table_name, "key")
                    # assert key_column != primary_key_metadata.iloc[0]["name"], \
                    #     "Table %s not keyed by the Survey's primary key" % table_name

                    # if table_name == primary_key_metadata.iloc[0]["definitive_table"]:
                    #     # This table contains the definitive list of object IDs
                    #     pass

                    assert key_column in column_metadata.index, \
                        "Table %s seems to be missing key column %s" % (table_name, key_column)

                    table_columns = []  # type: List[fidia.ColumnDefinition]

                    for column_name in column_metadata.index:
                        fidia_column = fidia.CSVTableColumn(
                            pjoin(data_release, group_dir, table_dir, table_name + ".csv"),
                            column_name, key_column, "#")
                        fidia_column.short_description = column_metadata.get_value(column_name, "description")
                        fidia_column.ucd = column_metadata.get_value(column_name, "ucd")
                        fidia_column.unit = column_metadata.get_value(column_name, "unit")

                        table_columns.append(fidia_column)

                    fidia_table = fidia.traits.TraitMapping(
                        fidia.traits.Table,
                        table_name,
                        [fidia.traits.TraitPropertyMapping(c.column_name, c.id) for c in table_columns]
                    )

                    group_tables.append(fidia_table)

                    catalog_columns.extend(table_columns)

                fidia_group = fidia.traits.TraitMapping(
                    fidia.traits.DMU,
                    group_name,
                    group_tables
                )

                catalog_mappings.append(fidia_group)

            # print(json.dumps([mapping.as_specification_dict() for mapping in catalog_mappings], indent=2))
            # print(catalog_columns)

            self.trait_mappings.extend(catalog_mappings)
            # self.column_definitions.extend(catalog_columns)
            self.column_definitions = fidia.ColumnDefinitionList(catalog_columns)

        object_metadata = meta_data_loader(pjoin(basepath, data_release), self.archive_id, "astro_objects_meta")

        self.contents = list(object_metadata.index)