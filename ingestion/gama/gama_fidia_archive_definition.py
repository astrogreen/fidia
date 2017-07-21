
from typing import List

import fidia

from fidia.ingest.data_finder import *
from fidia.column import ColumnDefinitionList
from fidia.traits import *

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

def table_mappings_for_dumu(dmu_id):

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

        mappings, columns = table_mappings_for_dumu(row['DMUID'])

        trait_mappings.append(
            TraitMapping(DMU, row["name"],
                         mappings,
                         long_desc=row["shortDescription"])
        )

        all_columns.extend(columns)

    return trait_mappings, all_columns

def write_specification_dict_as_json(specification_dict, json_filename):
    with open(json_filename, "w") as f:
        json.dump(specification_dict, f, indent=4)

if __name__ == "__main__":

    mappings, columns = build_traitmapping_from_gama_database()

    specification_dict = [mapping.as_specification_dict(columns) for mapping in mappings]


    write_specification_dict_as_json(specification_dict, "/Users/agreen/Desktop/gama-datacentral.json")