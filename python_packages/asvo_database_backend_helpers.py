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

        # Collect the meta data

        #self.cursor.execute("DESCRIBE dmus")
        #columns = [row[0] for row in self.cursor]
        columns = OrderedDict({"name": "`tables`.`name`",
                               "catalogId": "`tables`.`tableid`",
                               "version": "`tables`.`version`",
                               "DMU": "`DMUs`.`name`",
                               "description": "`tables`.`shortDescription`",
                               "dmu_description": "`DMUs`.`shortdescription`",
                               "contact": "`tables`.`contact`"
                               })

        self.cursor.execute(
            """SELECT {columns}
            FROM `tables` JOIN `DMUs` ON (`tables`.`DMUID` = `DMUs`.`dmuid` )
            WHERE tables.name = '{table_name}'""".format(
            columns=", ".join(columns.values()),
            table_name=table_name))

        data = self.cursor.fetchall()
        if len(data) != 1:
            print("Data not the right length:")
            for i, d in enumerate(data):
                print("    " + str(i) + ": " + str(d))
            assert len(data) != 1, "Multiple or no GAMA tables found for table name '%s'" % table_name

        gama_table = dict()
        for column, value in zip(columns, data[0]):
            gama_table[column] = value



        # Collect information on the columns

        columns = ("columnid", "tableid", "name", "units", "ucd", "description")

        self.cursor.execute("SELECT {columns} FROM columns WHERE tableid = '{tableid}'".format(
            columns=", ".join(columns),
            tableid=gama_table['catalogId']))
        column_info = list()
        for cid, row in enumerate(self.cursor):
            column_dict = {col: value for col, value in zip(columns, row)}
            column_info.append(column_dict)

        gama_table['columns'] = column_info

        self.table_description_cache[table_name] = gama_table

        return gama_table

def get_gama_database_as_json():

    schema = []
    for table in GAMADatabase.tables:
        schema.append(GAMADatabase.describe_gama_table(table))

    return json.dumps(schema)

def add_sami_tables_to_json(json):


if __name__ == '__main__':
    print("\n\nTables found are:")
    for t in GAMADatabase.tables:
        print("   " + t)
    desc = GAMADatabase.describe_gama_table("StellarMasses")
    print("\n\nDescription of StellarMasses:")
    for r in desc:
        print("    " + r + ": " + str(desc[r]))
