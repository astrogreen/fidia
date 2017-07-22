"""

G A M A   I n g e s t e r   f o r   F I D I A



This produces several archives to support GAMA DR2 data in FIDIA.

The main archive is indexed by GAMA CATAID, and has all of the data that can be
directly identified for each object.

"""

# noinspection PyUnresolvedReferences
from typing import List
# noinspection PyUnresolvedReferences
import fidia

from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList
from fidia.traits import *

from fidia.ingest.ingestion_helpers import *

from sqlalchemy import create_engine

engine = create_engine("mysql+mysqldb://agreen:agreen@10.80.10.137/dr2")

connection = engine.connect()

def collect_columns(table_id):

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

        col = SourcelessColumn("GAMA:%s:%s" % (row["tableID"], row["columnID"]),
                               unit=row['units'], ucd=row['ucd'], long_desc=row['description'])
        columns.add(col)

        mappings.append(TraitPropertyMapping(row['name'], col.id))

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
            continue

        mappings, columns = collect_columns(row["tableID"])

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

    mappings, columns = build_traitmapping_from_gama_database()

    specification_dict = dict()
    for mapping in mappings:
        specification_dict.update(mapping.as_specification_dict(columns))

    json_output_path = os.path.join(os.path.dirname(__file__), "gama-datacentral.json")
    write_specification_dict_as_json(specification_dict, json_output_path)

    validation_error_output_path = os.path.join(os.path.dirname(__file__), "gama-datacentral-errors.txt")
    write_validataion_errors(specification_dict, validation_error_output_path)