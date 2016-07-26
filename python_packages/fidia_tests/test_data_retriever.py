from pandas import DataFrame

from fidia.cache.data_retriver import DataRetriever


class TestDataRetriver():

    def test_getTraitPropertyByObjectId(self):

        object_id = 'Gal1'

        # scenario 1
        trait_key = 'velocity_map'
        trait_property_name = 'value'
        trait_property_type = 'array'

        data = DataRetriever().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name, trait_property_type)

        assert isinstance(data, DataFrame)
        #
        # scenario 2
        trait_key = 'velocity_map'
        trait_property_name = 'variance'
        trait_property_type = 'array'

        data = DataRetriever().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name, trait_property_type)

        assert isinstance(data, DataFrame)

        # scenario 3
        trait_key = 'spectral_map'
        trait_property_name = 'total_exposure'

        data = DataRetriever().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)

        assert isinstance(data, DataFrame)

        # scenario 4
        trait_key = 'spectral_map'
        trait_property_name = 'cubing_code_version'

        data = DataRetriever().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)

        assert isinstance(data, DataFrame)