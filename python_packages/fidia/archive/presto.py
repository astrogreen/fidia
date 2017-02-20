
__author__ = "Lloyd Harischandra"

import requests
import time

from hdfs import Config, InsecureClient
from hdfs.ext.avro import AvroReader

class PrestoArchive():

    def __init__(self):
        self.__headers = {
                            "X-Presto-Catalog": "hive",
                            "X-Presto-Schema":  "asvo",
                            "User-Agent":       "myagent",
                            "X-Presto-User":    "lharischandra"
                            }

        self.__url = 'http://asvotest1.aao.gov.au:8092/v1/execute'


    def execute_query(self, query, database=None):

        self.__headers.update({"X-Presto-Schema": database})
        result = requests.post(self.__url, data=query, headers=self.__headers)
        #r = requests.get(url, data={})
        return result


    def get_columnnames(self, table):
        result = self.execute_query("Describe " + table)
        if result.ok:
            return result.json()['data']
        else:
            return result.status_code + result.reason


    def get_tablenames(self):
        result = self.execute_query("Show tables")
        if result.ok:
            return result.json()['data']
        else:
            return result.status_code + result.reason


    def get_dmu_data(self):
        result = self.execute_query("Select * from DMUs", "default")
        if result.ok:
            return result.json()
        else:
            return result.status_code + result.reason

    def get_tables_by_dmu(self, dmuid):
        result = self.execute_query("Select * from tables where dmuid=" + str(dmuid), "default")
        if result.ok:
            return result.json()
        else:
            return result.status_code + result.reason

    def get_columns_by_table(self, tableid):
        result = self.execute_query("Select * from columns where tableid=" + str(tableid), "default")
        if result.ok:
            return result.json()
        else:
            return result.status_code + result.reason

    def get_sql_schema(self):
        dmu_data = self.get_dmu_data()
        dmus_list = list()
        for dmu in dmu_data['data']:
            dmu_dict = dict()
            dmu_id = dmu[0]
            dmu_dict['name'] = dmu[1]
            table_data = self.get_tables_by_dmu(dmu_id)
            tables_list = list()
            for tbl in table_data['data']:
                table = dict()
                table_id = tbl[0]
                table['name'] = tbl[1]
                table['version'] = tbl[4]
                table['shortdescription'] = tbl[7]
                column_data = self.get_columns_by_table(table_id)
                columns_list = list()
                for col in column_data['data']:
                    column = dict()
                    column['name'] = col[2]
                    meta = dict()
                    meta['ucd'] = col[4]
                    meta['description'] = col[5]
                    column['meta'] = meta
                    columns_list.append(column)
                table['cols'] = columns_list
                tables_list.append(table)
            dmu_dict['cats'] = tables_list
            dmus_list.append(dmu_dict)

        return dmus_list


    def getSpectralMapsById(self, object_id):
        #query = "Select object_id, map_keys(red) from sami_spectral_maps where object_id='" + object_id + "'"

        # query = "select object_id, val.value.datavalues, val.value.shape, val.variance.datavalues, val.variance.shape" \
        #         " from sami_line_maps CROSS JOIN unnest(halpha) as t (key, val) where object_id='278802' and key='recom_comp-V02'"

        query = "Select object_id, red['No_branch'].weight from sami_spectral_maps where object_id='551202'"

        result = self.execute_query(query)
        if result.ok:
            json = result.json()
            data = json['data']
            result.close()
        else:
            str = str(result.status_code) + result.reason
            result.close()
            return str

    def getSpectralMapTraitPropertyById(self, property_name, object_id):
        """
        This is an example method to show how to get an spectral map's trait property from a path
        when only the path is stored in the database.
        :param property_name: name of the trait property. i.e value, variance etc.
        :param object_id:
        :return:
        """
        query = "select object_id, blue['No_branch']." + property_name + " as " + property_name + \
                " from sami_spectral_maps where object_id='" + object_id + "'"

        result = self.execute_query(query)
        if result.ok:
            json_data = result.json()
            # for row in json_data['data']:
            #     index = 0
            #     for column in json_data['columns']:
            #         if column['name'] in ['value', 'variance', 'covariance', 'weight']:
            #             value = self.get_trait_property_data(row[index])
            #             row.pop(index)
            #             row.insert(index, value[0])
            #         index += 1

            data = self.doRecursiveQuery(result)
            columns = json_data['columns']
            result.close()
            return data
        else:
            result.close()
            return None

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


    def get_trait_property_data(self, path):
        with AvroReader(self.get_hdfs_client(), "/user/lharischandra/" + path) as reader:
            schema = reader.schema
            content = reader.content
            data = list()
            for record in reader:
                data.append(record['data'])
            return data


    def get_hdfs_client(self):
        return InsecureClient("http://asvotest1.aao.gov.au:50070", user="lharischandra")
