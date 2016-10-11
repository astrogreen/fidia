
from fidia import traits
from fidia.cache import Cache
from fidia import exceptions

import requests

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

class PrestoCache(Cache):

    trait_to_table_mapping = {
        'extinction_map': "sami_extinction_maps",
        'velocity_map': "sami_velocity_maps",
        # "sami_spectral_map_paths",
        'line_emission_map': "sami_line_maps",
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
        """Execute the given query against the Presto DB RESTful endpoint and return `requests.Response` object."""
        result = requests.post(self.__url, data=query, headers=self.__headers)
        return result


    def get_columnnames(self, table):
        """Return a list of column names in the given table."""
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
        """Retrieve the value of a trait_property from the database.

        Implementation:

            - Identify the database table containing the relevant data.
            - Construct the column name pointing to the particular branch,
              version, and then sub-trait and trait-property requested.
            - Run the query against the database
            - Extract the result and return it.

        """

        top_level_trait_key = traits.TraitKey.as_traitkey(trait_key_path[0])

        # Get the name of the table to be queried:
        # @TODO: If the table names are standardized, change this to match the standard.
        try:
            # Look up the table name in the mapping from trait_type to table name.
            table_name = self.trait_to_table_mapping[top_level_trait_key.trait_type]
        except KeyError:
            # Trait type not found in the mapping, so no data avilable.
            raise exceptions.DataNotAvailable("PrestoCache has no table for '%s'" % top_level_trait_key.trait_type)

        # Construct the column name from the first element of the Trait path.
        column_name = "{qualifier}['{branch}-{version}']".format(
            qualifier=top_level_trait_key.trait_qualifier,
            branch=top_level_trait_key.branch,
            version=top_level_trait_key.version)
        # Extend the column name for subsequent levels of the path if necessary
        for key in trait_key_path[1:]:
            tk = traits.TraitKey(key)
            column_name += ".{trait_name}".format(trait_name=tk.trait_name)

        # Extend the column name with the trait_property name
        column_name += ".{tp_name}".format(tp_name=trait_property_name)

        # Construct the query
        query = "SELECT object_id, {column_name} AS data FROM {table_name} WHERE object_id='{object_id}'".format(
            column_name=column_name, table_name=table_name, object_id=object_id
        )

        # Execute the query
        result = self.execute_query(query)
        if result.ok:
            json_data = result.json()

            # the 'data' key has the actual result of the query
            # the 'columns' key has information about the returned columns

            if len(json_data['data']) != 1:
                # Returned too many results?
                log.error("Presto DB cache query returned too many results?!")
                # @TODO: Should this raise an exception?
                pass

            # Split the row into its elements
            returned_object_id, data = json_data['data'][0]

            # Confirm that the data returned is as expected.
            assert returned_object_id == object_id

            return data
        else:
            log.info("Presto DB query failed for query '%s'", query)
            raise exceptions.DataNotAvailable("Presto DB query failed for query '%s'" % query)



    def check_trait_property_available(self, object_id, trait_key_path, trait_property_name):
        """A fast check if a cache request for the given data is likely to bear fruit."""
        top_level_trait_key = traits.TraitKey.as_traitkey(trait_key_path[0])

        # @TODO: If the table names are standardized, change this to match the standard.
        return top_level_trait_key.trait_type in  self.trait_to_table_mapping