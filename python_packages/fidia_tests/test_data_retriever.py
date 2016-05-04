from pandas import DataFrame

from fidia.cache.data_retriver import DataRetriver


class TestDataRetriver():

    def test_getTraitPropertyByObjectId(self):

        # scenario 1
        object_id = 'Gal1'
        trait_key = 'simple_trait'
        trait_property_name = 'extra'

        data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)

        assert isinstance(data, DataFrame)


        # # scenario 2
        # object_id = 'Gal1'
        # trait_key = 'simple_trait'
        # trait_property_name = 'value' #
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 3
        # trait_key = 'redshift'
        # trait_property_name = 'value'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 4
        # trait_key = 'velocity_map'
        # trait_property_name = 'value.shape'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 5
        # trait_key = 'velocity_map'
        # trait_property_name = 'value.datavalues.item'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # scenario 6
        trait_key = 'velocity_map'
        trait_property_name = 'variance'
        trait_property_type = 'array'

        data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name, trait_property_type)

        assert isinstance(data, DataFrame)
        #
        # # scenario 7
        # trait_key = 'velocity_map'
        # trait_property_name = 'variance.datavalues'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 8
        # trait_key = 'spectral_map'
        # trait_property_name = 'value.shape'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 9
        # trait_key = 'spectral_map'
        # trait_property_name = 'value.datavalues'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 10
        # trait_key = 'spectral_map'
        # trait_property_name = 'variance.shape'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # # scenario 11
        # trait_key = 'spectral_map'
        # trait_property_name = 'variance.datavalues'
        #
        # data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)
        #
        # assert isinstance(data, DataFrame)
        #
        # scenario 12
        trait_key = 'spectral_map'
        trait_property_name = 'galaxy_name'

        data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)

        assert isinstance(data, DataFrame)

        # scenario 13
        trait_key = 'spectral_map'
        trait_property_name = 'extra_value'

        data = DataRetriver().getTraitPropertyByObjectId(object_id, trait_key, trait_property_name)

        assert isinstance(data, DataFrame)