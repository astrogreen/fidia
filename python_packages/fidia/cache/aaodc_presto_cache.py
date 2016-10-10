
from fidia import traits
from fidia.cache import Cache
from fidia.exceptions import DataNotAvailable, ReadOnly

import requests

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()
# log.setLevel(slogging.WARNING)

class PrestoCache(Cache):

    trait_to_table_mapping = {
        'extinction_map': "sami_extinction_maps",
        'velocity_map': "sami_velocity_maps",
        # "sami_spectral_map_paths",
        'line_map': "sami_line_maps",
        'sfr_cube': "sami_sfr_maps"
    }

    def __init__(self, parquet_path=None, **kwargs):

        log.debug("Initialising PrestoCache...")

        # Headers to authenticate against the RESTful interface.
        self.__headers = {
                            "X-Presto-Catalog": "hive",
                            "X-Presto-Schema":  "asvo",
                            "User-Agent":       "myagent",
                            "X-Presto-User":    "lharischandra"
                            }

        # RESTful URL for accessing the PrestoDB execution engine
        self.__url = 'http://asvotest1.aao.gov.au:8092/v1/execute'

        super(PrestoCache, self).__init__(**kwargs)


    def execute_query(self, query):
        """Execute the given query against the Presto DB RESTful endpoint"""
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

    def get_cached_trait_property(self, object_id, trait_key_path, trait, trait_property_name):
        # get the path to the Trait if interest in the format we want:


        # Top level trait_key
        top_level_trait_key = traits.TraitKey.as_traitkey(trait_key_path[0])


        # The first element in the path will contain the branch and version information
        branch = top_level_trait_key.branch
        version = top_level_trait_key.version


        try:
            table_name = self.trait_to_table_mapping[top_level_trait_key.trait_type]
        except KeyError:
            raise DataNotAvailable

        # First level of hierarchy
        column_name = "{qualifier}['{branch}']".format(qualifier=top_level_trait_key.trait_qualifier,
                                                       branch=top_level_trait_key.branch)
        # Add subsequent levels of path heirarchy (if needed)
        for key in trait_key_path[1:]:
            tk = traits.TraitKey(key)
            column_name += ".{trait_name}".format(trait_name=tk.trait_name)

        # Add trait_property name
        column_name += ".{tp_name}".format(tp_name=trait_property_name)


        query = "select object_id, " + column_name + " as data " \
                " from " + table_name + " where object_id='" + object_id + "'"

        result = self.execute_query(query)
        if result.ok:
            json_data = result.json()

            # the 'data' key has the actual result of the query:

            if len(json_data['data']) > 1:
                # Returned too many results?
                log.error("Presto DB cache query retrned too many results?!")
                pass



            return json_data['data']['data']
        else:
            raise DataNotAvailable



    def check_trait_property_available(self, object_id, trait_key_path, trait_property_name):

        # e.g. check that the schema contains data for the given path, and if not, return False.
        #
        # if trait_key_path not in parquet.schema:
        #     return False
        return True