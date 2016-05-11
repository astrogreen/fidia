from impala.dbapi import connect
from impala.util import as_pandas



class DataRetriver():

    def __init__(self):
        self.conn = connect('asvotest2.aao.gov.au', 21050, 'sami_test')
        self.cursor = self.conn.cursor()


    def getTraitPropertyByObjectId(self, object_id, trait_key, trait_property_name, trait_property_type=''):
        '''
        Search trait property by object id
        :param object_id:
        :param trait_key: Name of the trait, e.g redshift
        :param trait_property_name: Name of the trait property, e.g. value, variance etc.
        :param trait_property_type: If it's an array, put array. Otherwise use the default which is
        an empty string.
        :return: A pandas dataframe containing the result set.
        '''

        # parameterized queries don't work here.

        table_name = 'sami_test2_5_parquet'

        if 'array' in trait_property_type:
            query = 'Select value.' + trait_property_name + '.shape, item from ' + table_name + ',' + table_name + '.' + trait_key + ',' \
                          + table_name + '.' + trait_key + '.value.' + trait_property_name + '.datavalues where object_id="' + object_id + '"'
        else:
            query = 'Select ' + trait_property_name + ' from ' + table_name + ',' + table_name + '.' + trait_key + ' where object_id="' + object_id + '"'


        self.cursor.execute(query)
        df = as_pandas(self.cursor)
        self.cursor.close()
        return df










