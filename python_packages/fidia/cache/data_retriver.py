from impala.dbapi import connect
from impala.util import as_pandas



class DataRetriever():

    def __init__(self):
        self.conn = connect('asvotest2.aao.gov.au', 21050, 'sami_test')
        self.cursor = self.conn.cursor()
        self.table_name = 'astro_sample_9' #'sami_test2_5_parquet'


    def getTraitPropertyByObjectId(self, object_id, trait_key, trait_property_name, trait_property_type=''):
        """
        Search trait property by object id
        :param object_id:
        :param trait_key: Name of the trait, e.g redshift
        :param trait_property_name: Name of the trait property, e.g. value, variance etc.
        :param trait_property_type: If it's an array, put array. Otherwise use the default which is
        an empty string.
        :return: A pandas dataframe containing the result set.
        """

        # parameterized queries don't work here.


        if 'array' in trait_property_type:
            query = 'Select value.' + trait_property_name + '.shape, item from ' + self.table_name + ',' + self.table_name + '.' + trait_key + ',' \
                          + self.table_name + '.' + trait_key + '.value.' + trait_property_name + '.datavalues where object_id="' + object_id + '"'
        else:
            query = 'Select ' + trait_property_name + ' from ' + self.table_name + ',' + self.table_name + '.' + trait_key + ' where object_id="' + object_id + '"'


        self.cursor.execute(query)
        df = as_pandas(self.cursor)
        self.cursor.close()
        return df


    def sql(self, query):
        """
        Execute a sql query and return the results list
        :param query: sql string
        :return: a list of tuples
        """
        self.cursor.execute(query)
        assert isinstance(self.cursor, object)
        results = self.cursor.fetchall()
        self.cursor.close()
        return results








