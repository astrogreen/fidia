"""

G A M A   I n g e s t e r   f o r   F I D I A



This produces a FIDIA Archive definition for GAMA.

As the final steps, it creates an instance of this archive (which will "ingest"
it into the persistance database if `is_persisted = True`, and retrieves a piece
of data using this instance.

The main archive is indexed by GAMA CATAID. Currently, no tables that are not
uniquely indexed by CATAID are included. (The code ignores tables where CATAID
is not the primary key)

This will need to be extended to several archives to include Group data (those
archives will be indexed by e.g. GroupID).

Furthermore, the main archive will need to be extended to include data not
indexed directly by CATAID (i.e. it must add "JOIN"ed data.)

"""

from typing import List
import fidia

import os

# from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList, SQLColumn, ColumnDefinition
from fidia.traits import *

from fidia.ingest.ingestion_helpers import *

from sqlalchemy import create_engine

from fidia import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.INFO)
log.enable_console_logging()



engine = create_engine("mysql+mysqldb://agreen:agreen@10.80.10.137/dr2")

connection = engine.connect()

alias_idx = 1

def collect_columns(table_id, index_column):

    global alias_idx

    mappings = []  # type: List[TraitPropertyMapping]
    columns = ColumnDefinitionList()

    results = connection.execute("SELECT * FROM `columns` WHERE `tableID` = %s" % table_id)
    # @SECURITY: Not secure if table_id is not sensible.

    # +-------------+------------------+------+-----+---------+----------------+
    # | Field       | Type             | Null | Key | Default | Extra          |
    # +-------------+------------------+------+-----+---------+----------------+
    # | columnID    | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    # | tableID     | int(10) unsigned | NO   | MUL | NULL    |                |
    # | name        | varchar(50)      | NO   |     | NULL    |                |
    # | units       | varchar(30)      | NO   |     | NULL    |                |
    # | ucd         | varchar(100)     | NO   | MUL | NULL    |                |
    # | description | text             | NO   |     | NULL    |                |
    # +-------------+------------------+------+-----+---------+----------------+

    for row in results:

        table_data = connection.execute("SELECT * FROM tables WHERE tableID = %s" % table_id).fetchone()

        if row['units'] == "-":
            unit = ""
        else:
            unit = row['units']

        col_alias = "Col" + str(alias_idx)
        alias_idx += 1
        col = SQLColumn(
            "SELECT {index_column} as `id`, {data_column} as `data` FROM {table}".format(
                index_column=index_column, data_column=row["name"], table=table_data["name"]),
            unit=unit, ucd=row['ucd'], long_description=row['description'])
        columns.add((col_alias, col))

        mappings.append(TraitPropertyMapping(row['name'], col_alias))

    return mappings, columns

def cataid_table_mappings_for_dumu(dmu_id):
    """Create Mappings for all tables in the DMU that are uniquely indexed by CATAID"""
    table_mappings = []  # type: List[TraitMapping]
    all_columns = ColumnDefinitionList()

    results = connection.execute("SELECT * FROM `tables` WHERE `DMUID` = %s" % dmu_id)
    # @SECURITY: Not secure if dmu_id is improperly formatted.

    # +------------------+------------------+------+-----+---------+----------------+
    # | Field            | Type             | Null | Key | Default | Extra          |
    # +------------------+------------------+------+-----+---------+----------------+
    # | tableID          | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    # | name             | varchar(100)     | NO   | MUL | NULL    |                |
    # | contact          | varchar(100)     | NO   |     | NULL    |                |
    # | date             | date             | NO   |     | NULL    |                |
    # | version          | char(3)          | NO   | MUL | NULL    |                |
    # | newest           | tinyint(1)       | NO   | MUL | NULL    |                |
    # | DMUID            | int(10) unsigned | NO   | MUL | NULL    |                |
    # | shortDescription | text             | NO   |     | NULL    |                |
    # | filename         | varchar(255)     | NO   |     | NULL    |                |
    # | url              | varchar(255)     | NO   |     | NULL    |                |
    # | viewof           | varchar(255)     | NO   |     | NULL    |                |
    # +------------------+------------------+------+-----+---------+----------------+


    for row in results:

        # Check if table is uniquely indexed by CATAID:
        index_result = connection.execute(
            "SHOW INDEXES FROM %s WHERE `column_name` = 'CATAID' AND key_name = 'PRIMARY'" % row["name"])
        if index_result.rowcount != 1:
            log.info("    skipping table %s (no CATAID is not the Primary Key).", row["name"])
            continue

        log.info("    Processing table %s...", row["name"])


        mappings, columns = collect_columns(row["tableID"], "CATAID")

        all_columns.extend(columns)

        table_mappings.append(
            TraitMapping(Table, row["name"],
                         mappings,
                         long_desc=row["shortDescription"])
        )

    return table_mappings, all_columns

def build_traitmapping_from_gama_database():

    trait_mappings = []  # type: List[TraitMapping]
    all_columns = ColumnDefinitionList()  # type: List[ColumnDefinition]

    dmu_results = connection.execute("SELECT * FROM `DMUs`")

    # +------------------+------------------+------+-----+---------+----------------+
    # | Field            | Type             | Null | Key | Default | Extra          |
    # +------------------+------------------+------+-----+---------+----------------+
    # | DMUID            | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
    # | name             | varchar(100)     | NO   | MUL | NULL    |                |
    # | contact          | varchar(100)     | NO   |     | NULL    |                |
    # | date             | date             | NO   |     | NULL    |                |
    # | version          | char(3)          | NO   | MUL | NULL    |                |
    # | newest           | tinyint(1)       | NO   | MUL | NULL    |                |
    # | sort_order       | int(11)          | YES  | MUL | NULL    |                |
    # | shortDescription | text             | NO   |     | NULL    |                |
    # | path             | varchar(255)     | NO   |     | NULL    |                |
    # | url              | varchar(255)     | NO   |     | NULL    |                |
    # | paperID          | int(11)          | NO   |     | 0       |                |
    # +------------------+------------------+------+-----+---------+----------------+

    for row in dmu_results:

        log.info("Processing DMU %s...", row["name"])

        # if row["name"] != "StellarMasses":
        #     continue

        mappings, columns = cataid_table_mappings_for_dumu(row['DMUID'])

        if len(mappings) == 0:
            # There were no tables indexed by CATAID.
            continue

        trait_mappings.append(
            TraitMapping(DMU, row["name"],
                         mappings,
                         long_desc=row["shortDescription"])
        )

        all_columns.extend(columns)

    return trait_mappings, all_columns


if __name__ == "__main__":

    main_mappings, main_columns = build_traitmapping_from_gama_database()

    specification_dict = dict()
    for mapping in main_mappings:
        specification_dict.update(mapping.as_specification_dict(main_columns))

    json_output_path = os.path.join(os.path.dirname(__file__), "gama-datacentral.json")
    write_specification_dict_as_json(specification_dict, json_output_path)

    validation_error_output_path = os.path.join(os.path.dirname(__file__), "gama-datacentral-errors.txt")
    write_validataion_errors(specification_dict, validation_error_output_path)

    class GAMAArchive(fidia.ArchiveDefinition):

        archive_id = "GAMA_DR2"
        archive_type = fidia.DatabaseArchive

        column_definitions = main_columns

        trait_mappings = main_mappings

        contents = [row["CATAID"] for row in connection.execute("SELECT CATAID FROM DistancesFrames")]
        # contents = ["24433"]

        is_persisted = True

    ar = GAMAArchive(database_url="mysql+mysqldb://agreen:agreen@10.80.10.137/dr2")  # type: fidia.Archive

    print(ar["24433"].dmu["StellarMasses"].table["StellarMasses"].logmstar)


