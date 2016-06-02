
from fidia.cache import Cache
from fidia.exceptions import DataNotAvailable, ReadOnly


class AAODC_Parquet_Cache(Cache):

    def __init__(self, parquet_path=None, **kwargs):

        # Open connection to parquet file...

        # Other initialisation...

        super(AAODC_Parquet_Cache, self).__init__(**kwargs)

    def get_cached_trait_property(self, object_id, trait_key_path, trait_property_name):
        # get the path to the Trait if interest in the format we want:

        version = "v1"
        branch = "b1"

        # Get the right astro_object:
        astro_object = parquet.read_for_id(object_id)

        # Step down the parquet hierarchy for this object, correctly handling the top level
        trait_data = None
        for trait_key in trait_key_path:
            if trait_data is None:
                # We are at the top level, so handle version, etc.
                trait_data = astro_object.getData(branch + "_" + version)
                trait_data.getData(trait_key.trait_type)
            else:
                # We're looking for a sub_trait
                trait_data = trait_data.getData(trait_key.trait_type)

        # Get the trait_property data:
        trait_property_data = trait_data.getValue(trait_property_name)

        # Handle arrays...?

        return trait_property_data



    def check_trait_property_available(self, object_id, trait_key_path, trait_property_name):

        # e.g. check that the schema contains data for the given path, and if not, return False.
        #
        # if trait_key_path not in parquet.schema:
        #     return False
        pass