import json
from collections import OrderedDict
from impala.dbapi import connect
from MySQLdb import connect as mysqlconnect

from cached_property import cached_property


def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance


@singleton
class GAMADatabase:

    table_meta_data_columns = OrderedDict({
            "name": "`tables`.`name`",
            "catalogId": "`tables`.`tableid`",
            "version": "`tables`.`version`",
            "DMU": "`DMUs`.`name`",
            "description": "`tables`.`shortDescription`",
            "dmu_description": "`DMUs`.`shortdescription`",
            "contact": "`tables`.`contact`"
            })

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.table_description_cache = dict()

    def open_connection(self):
        # self.conn = connect(host='asvotest1.aao.gov.au', port=10000, auth_mechanism='PLAIN')
        self.conn = mysqlconnect(host='10.80.10.137', user='agreen', passwd='agreen', db='dr2')
        self.cursor = self.conn.cursor()

    @cached_property
    def tables(self):
        if self.conn is None:
            self.open_connection()

        self.cursor.execute("SELECT `name` FROM `tables` WHERE `tableid` IS NOT NULL")
        tables = [row[0] for row in self.cursor]
        return tables

    @cached_property
    def dmus(self):
        if self.conn is None:
            self.open_connection()

        self.cursor.execute("SELECT `name` FROM `DMUs` WHERE `DMUID` IS NOT NULL")
        dmus = [row[0] for row in self.cursor]
        return dmus

    def describe_gama_table(self, table_name):

        if table_name in self.table_description_cache:
            return self.table_description_cache[table_name]

        if self.conn is None:
            self.open_connection()
        if table_name not in self.tables:
            raise ValueError("Table '%s' not in GAMA database" % table_name)


        # Collect the table meta data

        self.cursor.execute(
            """SELECT {columns}
            FROM `tables` JOIN `DMUs` ON (`tables`.`DMUID` = `DMUs`.`dmuid` )
            WHERE tables.name = '{table_name}'""".format(
            columns=", ".join(self.table_meta_data_columns.values()),
            table_name=table_name))

        data = self.cursor.fetchall()
        if len(data) != 1:
            print("Data not the right length:")
            for i, d in enumerate(data):
                print("    " + str(i) + ": " + str(d))
            assert len(data) != 1, "Multiple or no GAMA tables found for table name '%s'" % table_name

        gama_table = dict()
        for column, value in zip(self.table_meta_data_columns, data[0]):
            gama_table[column] = value

        gama_table['columns'] = self.get_column_data(gama_table['catalogId'])

        self.table_description_cache[table_name] = gama_table

        return gama_table


    def get_column_data(self, catalog_id):
        """Collect information on the columns in GAMA table identified by catalog_id"""
        columns = ("columnid", "tableid", "name", "units", "ucd", "description")

        self.cursor.execute("SELECT {columns} FROM columns WHERE tableid = '{tableid}'".format(
            columns=", ".join(columns),
            tableid=catalog_id))
        column_info = list()
        for cid, row in enumerate(self.cursor):
            column_dict = {col: value for col, value in zip(columns, row)}
            column_info.append(column_dict)

        return column_info




def get_gama_database_as_json():

    schema = []
    for table in GAMADatabase.tables:
        schema.append(GAMADatabase.describe_gama_table(table))

    return json.dumps(schema)

def add_sami_tables_to_json(json_string):

    schema = json.loads(json_string)

    sami_table = dict()

    for key in GAMADatabase.table_meta_data_columns:
        sami_table[key] = None
    sami_table['name'] = "SAMI"
    sami_table['description'] = "Table containing SAMI sample with observation information"
    sami_table['contact'] = "Andy Green <andrew.green@aao.gov.au>"
    sami_table['version'] = "v01"
    sami_table['DMU'] = "SAMI"
    sami_table['catalogId'] = -1

    sami_table['columns'] = list()

    sami_table['columns'].append(
        {"columnid": -1,
         "description": "SAMI ID (matches GAMA ID when the same object)",
         "name": "sami_id",
         "tableid": -1,
         "ucd": "meta.id;",
         "units": "-"})

    sami_table['columns'].append(
        {"columnid": -1,
         "description": "Is a cube available in the database",
         "name": "cube_available",
         "tableid": -1,
         "ucd": "",
         "units": "-"})

    sami_table['columns'].append(
        {"columnid": -1,
         "description": "URL of the data browser for this object",
         "name": "data_browser_url",
         "tableid": -1,
         "ucd": "",
         "units": "-"})

    schema.append(sami_table)
    return json.dumps(schema)

if __name__ == '__main__':
    import sys, os.path
    print("\n\nTables found are:")
    for t in GAMADatabase.tables:
        print("   " + t)
    desc = GAMADatabase.describe_gama_table("StellarMasses")
    print("\n\nDescription of StellarMasses:")
    for r in desc:
        print("    " + r + ": " + str(desc[r]))

    print("\n\n")

    outfile = os.path.split(os.path.realpath(__file__))[0] + "/../web_application/restapi_app/gama_database.json"
    if len(sys.argv) > 1 and sys.argv[1] == 'write':
        json_to_write = add_sami_tables_to_json(get_gama_database_as_json())
        with open(outfile, 'w') as f:
            f.write(json_to_write)
        with open(outfile[:-5] + "_formatted.json", 'w') as f:
            f.write(json.dumps(json.loads(json_to_write), indent=2))

    else:
        print("Call with 'write' command to update {}".format(outfile))

