import sys
import json
from collections import OrderedDict

from py4j.java_gateway import JavaGateway
from py4j.protocol import Py4JError, Py4JJavaError, Py4JNetworkError

# from impala.dbapi import connect
# from MySQLdb import connect as mysqlconnect
import psycopg2
import sqlite3
import database_config as cfg
import logging
import traceback
import requests
import time

from cached_property import cached_property
from fidia.archive.presto import PrestoArchive

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance

class PrestDBException(Exception):
    def __init__(self, *args):
        self.message = args[0]
        self.status_code = args[1]

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
        # self.conn = mysqlconnect(host='10.80.10.137', user='agreen', passwd='agreen', db='dr2')
        # self.cursor = self.conn.cursor()
        pass

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


@singleton
class MappingDatabase:

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.local_conn = None
        self.local_cursor = None

    def open_connection(self):
        self.conn = psycopg2.connect(database=cfg.postgres_svr['db'], user=cfg.postgres_svr['user'],
                                     password=cfg.postgres_svr['passwd'], host=cfg.postgres_svr['host'])
        # database="aaodc", user="asvo", password="a1s9v8o4!P", host="asvotest1.aao.gov.au"
        # self.conn = mysqlconnect(host='10.80.10.137', user='agreen', passwd='agreen', db='dr2')
        self.cursor = self.conn.cursor()

    # use local connection temporarily until we move to one database
    def open_local_connection(self):
        if cfg.local_default is 'sqlite':
            self.local_conn = sqlite3.connect(cfg.local_sqlite['file'])
        elif cfg.local_default is 'postgres':
            self.local_conn = psycopg2.connect(database=cfg.local_postgres['db'], user=cfg.local_postgres['user'],
                                               password=cfg.local_postgres['passwd'], host=cfg.local_postgres['host'])
        self.local_cursor = self.local_conn.cursor()

    def get_group_data(self):
        if self.conn is None:
            self.open_connection()
        self.cursor.execute("Select * from groups;")
        one = self.cursor.fetchall()
        self.cursor.close()

    def get_catalogs_by_group(self, groupid):
        result = self.cursor.execute("Select * from catalogs where groupid=" + str(groupid))


    def get_columns_by_catalog(self, catalogid):
        result = self.cursor.execute("Select * from columns where catalogid=" + str(catalogid))


    def get_sql_schema(self):
        schema = dict()
        if self.conn is None:
            self.open_connection()
        self.cursor.execute("Select * from megatables;")
        megatables = self.cursor.fetchall()
        mt_list = list()
        for megatbl in megatables:
            mt_dict = dict()
            mt_dict['id'] = megatbl[0]
            mt_dict['name'] = megatbl[1]
            mt_dict['pretty_name'] = megatbl[2]
            self.cursor.execute("Select * from groups where groupid in (Select groupid from megatbl_group_link where "
                                "megaid={0});".format(megatbl[0]))
            groups = self.cursor.fetchall()
            group_list = list()
            for group in groups:
                group_dict = dict()
                group_dict['name'] = group[1]
                group_dict['contact'] = group[2]
                group_dict['date'] = group[3]
                group_dict['version'] = group[4]
                group_dict['description'] = group[7]
                self.cursor.execute("Select * from catalogs where groupid={0} and megaid={1};".format(group[0], megatbl[0]))
                catalogs = self.cursor.fetchall()
                cat_list = list()
                for cat in catalogs:
                    # for each catalog, find columns
                    cat_dict = dict()
                    cat_dict['name'] = cat[1]
                    cat_dict['contact'] = cat[2]
                    cat_dict['date'] = cat[3]
                    cat_dict['version'] = cat[4]
                    cat_dict['description'] = cat[7]
                    col_list = list()
                    self.cursor.execute("Select * from columns where catalogid={0};".format(cat[0]))
                    columns = self.cursor.fetchall()
                    for col in columns:
                        col_dict = dict()
                        col_dict['name'] = col[2]
                        col_dict['units'] = col[3]
                        col_dict['ucd'] = col[4]
                        col_dict['description'] = col[5]
                        col_list.append(col_dict)
                    cat_dict['columns'] = col_list
                    cat_list.append(cat_dict)
                group_dict['cats'] = cat_list
                group_list.append(group_dict)
            mt_dict['groups'] = group_list
            mt_list.append(mt_dict)
        schema['megatables'] = mt_list

        schema['post_joins'] = [{'name': 'gama', 'pretty_name': 'GAMA', 'megatbl_ids': [1]},
                                {'name': 'gama_mocks', 'pretty_name': 'GAMA Mock', 'megatbl_ids': [2]}]
        # self.cursor.close()
        return schema


    def execute_adql_query(self, query, results_tbl):
        """
        Connect to a Java gateway through py4j and invoke methods in ADQL translator.
        "Select InputCat.InputCatA.ra from gama where InputCat.InputCatA.dec=0.2 and redshift between 2 and 3"
        :param query:
        :return:
        """
        print(query)
        gateway = JavaGateway()
        try:
            mapped_query = gateway.entry_point.parseADQLQuery(query)
            if mapped_query is None:
                log.info("parser failed.")
                return None
        except (Py4JError, Py4JJavaError, Py4JNetworkError) as e:
            log.exception("Py4J exception occurred.")
            raise e
        try:
            mapped_query = "CREATE TABLE {0}.public.{1} AS {2}".format('adc_dev', results_tbl, mapped_query)
            result = PrestoArchive().execute_query(mapped_query, catalog='hive', schema='asvo')
            if result.ok:
                log.info("Ok I have successfully executed the query!")
                json_data = result.json()
                size = sys.getsizeof(json_data['data'])
                if(size/1024/1024 > 10):
                    log.error("Presto result exceeded the maximum size(10MB) allowed. size: {0}".format(
                            str(size/1024/1024) + "MB"))
                    raise PrestDBException("Query result exceeded the maximum size(10MB) allowed. size: {0}".format(
                    str(size/1024/1024) + "MB"), 501)
                return json_data
            else:
                log.error("Presto query failed :({0})".format(str(result.status_code) + result.text))
                raise PrestDBException(result.text, result.status_code)
        except (ConnectionError) as e:
            log.exception("Prestodb connection error occurred.")
            raise e

    data_list = list()
    def doRecursiveQuery(self, result):
        json_data = result.json()
        if 'data' in json_data:
            self.data_list.append(json_data['data'])
        if not 'nextUri' in json_data:
            if 'error' in json_data:
                #"query has failed"
                result.close()
                return json_data['error']
            else:
                #No nextUri, query has sucessfully finished.
                result.close()
                return self.data_list
        else:
            result = requests.get(json_data['nextUri'])
            if result.ok:
                self.doRecursiveQuery(result)
            elif result.status_code is 503:
                #wait 50-100ms
                time.sleep(0.075)
                self.doRecursiveQuery(result)
            else:
                #query failed
                result.close()
                return None

    def execute_sql_query(self, query, update=False):
        """
        Execute queries on a relational database.
        :param query:
        :return:
        """
        if self.local_conn is None:
            self.open_local_connection()
        self.local_cursor.execute(query)
        # self.local_cursor.execute("Update query_query set isCompleted = 1, results = '[a, b, c]' where id=19;")
        log.info("sql query executed.")
        if(update):
            self.local_conn.commit()
            log.info("update committed.")


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
    # print("\n\nTables found are:")
    # for t in GAMADatabase.tables:
    #     print("   " + t)
    # desc = GAMADatabase.describe_gama_table("StellarMasses")
    # print("\n\nDescription of StellarMasses:")
    # for r in desc:
    #     print("    " + r + ": " + str(desc[r]))
    #
    # print("\n\n")
    #
    # outfile = os.path.split(os.path.realpath(__file__))[0] + "/../web_application/restapi_app/gama_database.json"
    # if len(sys.argv) > 1 and sys.argv[1] == 'write':
    #     json_to_write = add_sami_tables_to_json(get_gama_database_as_json())
    #     with open(outfile, 'w') as f:
    #         f.write(json_to_write)
    #     with open(outfile[:-5] + "_formatted.json", 'w') as f:
    #         f.write(json.dumps(json.loads(json_to_write), indent=2))
    #
    # else:
    #     print("Call with 'write' command to update {}".format(outfile))

    # groups = MappingDatabase.get_group_data()
    # schema = MappingDatabase.get_sql_schema()
    # result = MappingDatabase.execute_adql_query("Select InputCat__InputCatA__CATAID as CATAID, InputCat__InputCatA__RA "
    #                                             "as RA from gama_mega_table where InputCat__InputCatA__DEC > 0.234")
    # print("done!")

    # result = MappingDatabase.execute_adql_query("SELECT StellarMasses__StellarMasses__CATAID FROM gama")

    # result = {"test": "data"}
    # query_id = 4
    # sql_qry = 'Update query_query set "isCompleted" = {0}, results = \'{1}\' where id={2};'.format(
    #         True, json.dumps(result), query_id)

    adql_qry = "Select DISTINCT InputCat__InputCatA__CATAID as CATAID, InputCat__InputCatA__RA " \
               "as RA from gama"# where InputCat__InputCatA__DEC > 0.234"

    a_q = "SELECT DISTINCT StellarMasses__StellarMasses__CATAID, StellarMasses__StellarMasses__Z, StellarMasses__StellarMasses__nQ, StellarMasses__StellarMasses__SURVEY_CODE, StellarMasses__StellarMasses__Z_TONRY, StellarMasses__StellarMasses__fluxscale, StellarMasses__StellarMasses__zmax_19p4, StellarMasses__StellarMasses__zmax_19p8, StellarMasses__StellarMasses__zmax_17p88, StellarMasses__StellarMasses__nbands, StellarMasses__StellarMasses__logmstar, StellarMasses__StellarMasses__dellogmstar, StellarMasses__StellarMasses__logmoverl_i, StellarMasses__StellarMasses__dellogmoverl_i, StellarMasses__StellarMasses__logage, StellarMasses__StellarMasses__dellogage, StellarMasses__StellarMasses__logtau, StellarMasses__StellarMasses__dellogtau, StellarMasses__StellarMasses__metal, StellarMasses__StellarMasses__delmetal, StellarMasses__StellarMasses__extBV, StellarMasses__StellarMasses__delextBV, StellarMasses__StellarMasses__logLWage, StellarMasses__StellarMasses__dellogLWage, StellarMasses__StellarMasses__gminusi, StellarMasses__StellarMasses__delgminusi, StellarMasses__StellarMasses__uminusr, StellarMasses__StellarMasses__deluminusr, StellarMasses__StellarMasses__gminusi_stars, StellarMasses__StellarMasses__uminusr_stars, StellarMasses__StellarMasses__C_logM_ur, StellarMasses__StellarMasses__C_logM_gi, StellarMasses__StellarMasses__C_logM_eBV, StellarMasses__StellarMasses__fitphot_u, StellarMasses__StellarMasses__delfitphot_u, StellarMasses__StellarMasses__absmag_u, StellarMasses__StellarMasses__delabsmag_u, StellarMasses__StellarMasses__absmag_u_stars, StellarMasses__StellarMasses__fitphot_g, StellarMasses__StellarMasses__delfitphot_g, StellarMasses__StellarMasses__absmag_g, StellarMasses__StellarMasses__delabsmag_g, StellarMasses__StellarMasses__absmag_g_stars, StellarMasses__StellarMasses__fitphot_r, StellarMasses__StellarMasses__delfitphot_r, StellarMasses__StellarMasses__absmag_r, StellarMasses__StellarMasses__delabsmag_r, StellarMasses__StellarMasses__absmag_r_stars, StellarMasses__StellarMasses__fitphot_i, StellarMasses__StellarMasses__delfitphot_i, StellarMasses__StellarMasses__absmag_i, StellarMasses__StellarMasses__delabsmag_i, StellarMasses__StellarMasses__absmag_i_stars, StellarMasses__StellarMasses__fitphot_z, StellarMasses__StellarMasses__delfitphot_z, StellarMasses__StellarMasses__absmag_z, StellarMasses__StellarMasses__delabsmag_z, StellarMasses__StellarMasses__absmag_z_stars, StellarMasses__StellarMasses__CATAID, StellarMasses__StellarMasses__Z, StellarMasses__StellarMasses__nQ, StellarMasses__StellarMasses__SURVEY_CODE, StellarMasses__StellarMasses__Z_TONRY, StellarMasses__StellarMasses__fluxscale, StellarMasses__StellarMasses__zmax_19p4, StellarMasses__StellarMasses__zmax_19p8, StellarMasses__StellarMasses__zmax_17p88, StellarMasses__StellarMasses__nbands, StellarMasses__StellarMasses__logmstar, StellarMasses__StellarMasses__dellogmstar, StellarMasses__StellarMasses__logmoverl_i, StellarMasses__StellarMasses__dellogmoverl_i, StellarMasses__StellarMasses__logage, StellarMasses__StellarMasses__dellogage, StellarMasses__StellarMasses__logtau, StellarMasses__StellarMasses__dellogtau, StellarMasses__StellarMasses__metal, StellarMasses__StellarMasses__delmetal, StellarMasses__StellarMasses__extBV, StellarMasses__StellarMasses__delextBV, StellarMasses__StellarMasses__logLWage, StellarMasses__StellarMasses__dellogLWage, StellarMasses__StellarMasses__gminusi, StellarMasses__StellarMasses__delgminusi, StellarMasses__StellarMasses__uminusr, StellarMasses__StellarMasses__deluminusr, StellarMasses__StellarMasses__gminusi_stars, StellarMasses__StellarMasses__uminusr_stars, StellarMasses__StellarMasses__C_logM_ur, StellarMasses__StellarMasses__C_logM_gi, StellarMasses__StellarMasses__C_logM_eBV, StellarMasses__StellarMasses__fitphot_u, StellarMasses__StellarMasses__delfitphot_u, StellarMasses__StellarMasses__absmag_u, StellarMasses__StellarMasses__delabsmag_u, StellarMasses__StellarMasses__absmag_u_stars, StellarMasses__StellarMasses__fitphot_g, StellarMasses__StellarMasses__delfitphot_g, StellarMasses__StellarMasses__absmag_g, StellarMasses__StellarMasses__delabsmag_g, StellarMasses__StellarMasses__absmag_g_stars, StellarMasses__StellarMasses__fitphot_r, StellarMasses__StellarMasses__delfitphot_r, StellarMasses__StellarMasses__absmag_r, StellarMasses__StellarMasses__delabsmag_r, StellarMasses__StellarMasses__absmag_r_stars, StellarMasses__StellarMasses__fitphot_i, StellarMasses__StellarMasses__delfitphot_i, StellarMasses__StellarMasses__absmag_i, StellarMasses__StellarMasses__delabsmag_i, StellarMasses__StellarMasses__absmag_i_stars, StellarMasses__StellarMasses__fitphot_z, StellarMasses__StellarMasses__delfitphot_z, StellarMasses__StellarMasses__absmag_z, StellarMasses__StellarMasses__delabsmag_z, StellarMasses__StellarMasses__absmag_z_stars FROM gama"

    ctq = "SELECT DISTINCT StellarMasses__StellarMasses__CATAID, StellarMasses__StellarMasses__Z, StellarMasses__StellarMasses__nQ from gama"

    # result = MappingDatabase.execute_sql_query(sql_qry, True)
    try:
        result = MappingDatabase.execute_adql_query(ctq, 'query_456')
    except Exception as e:
        log.debug("Caught raised error: ", e.toString())
    print("done!")