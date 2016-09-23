
__author__ = "Lloyd Harischandra"

import requests

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


    def execute_query(self, query):

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


    # def getSpectralMapsById(self, object_id):
    #     #query = "Select object_id, map_keys(red) from sami_spectral_maps where object_id='" + object_id + "'"
    #
    #     query = "select object_id, val.value.datavalues, val.value.shape, val.variance.datavalues, val.variance.shape" \
    #             " from sami_line_maps CROSS JOIN unnest(halpha) as t (key, val) where object_id='278802' and key='recom_comp-V02'"
    #
    #     result = self.execute_query(query)
    #     if result.ok:
    #         json = result.json()
    #         data = json['data']
    #         result.close()
    #     else:
    #         str = str(result.status_code) + result.reason
    #         result.close()
    #         return str

    def getSpectralMapTraitPropertyById(self, property_name, object_id):
        """
        This is an example method to show how to get an spectral map's trait property from a path
        when only the path is stored in the database.
        :param property_name: name of the trait property. i.e value, variance etc.
        :param object_id:
        :return:
        """
        query = "select object_id, red['No_branch']." + property_name + " as " + property_name + \
                " from sami_spectral_maps where object_id='" + object_id + "'"

        result = self.execute_query(query)
        if result.ok:
            json_data = result.json()
            for row in json_data['data']:
                index = 0
                for column in json_data['columns']:
                    if column['name'] in ['value', 'variance', 'covariance', 'weight']:
                        value = self.get_trait_property_data(row[index])
                        row.pop(index)
                        row.insert(index, value[0])
                    index += 1
            result.close()
            return json_data
        else:
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
