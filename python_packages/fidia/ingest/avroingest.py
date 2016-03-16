import sys

from fidia.archive import example_archive, archive
from fidia.traits.base_traits import Trait

from py4j.java_gateway import JavaGateway, GatewayParameters
from py4j.java_collections import MapConverter, ListConverter
from numpy import ndarray

import traceback


# 1. create schema - go through fidia schema and create avro schema - take the example_archive
# 2. create an avro object, iterate through sample, get trait keys, get trait and populate avro object.

ar = example_archive.ExampleArchive()
schema = ar.schema()

def main():
    ingestData(ar.get_full_sample(), schema)


def ingestData(sample, schema):
    gateway = JavaGateway()

    schema_string = createSchema(schema)
    astro_schema = gateway.entry_point.getSchema(schema_string)
    writer = gateway.entry_point.getParquetWriter(astro_schema)
    try:
        for object_id in sample:
            astro_record = gateway.entry_point.getDatum(astro_schema)
            astro_record.put("object_id", object_id)
            traits_found_for_this_object = False
            for trait_key in sample[object_id]:
                # if(trait_key.trait_type == 'simple_heir_trait' or trait_key.trait_type == 'spectral_map'):
                #     continue
                # Check that the Trait found is actually listed in the schema:
                assert trait_key.trait_type in schema

                trait = sample[object_id][trait_key]
                assert isinstance(trait, Trait)

                # Dictionary to store the data from the trait to be added to the database
                data_dict = dict()

                #This needs to be a if else for nested traits
                datum = gateway.entry_point.getDatum(astro_schema.getField(trait_key.trait_type).schema().getValueType())

                # Iterate and put values
                trait_schema = schema[trait_key.trait_type]
                for trait_property_name in trait_schema:
                    if isinstance(trait_schema[trait_property_name], dict):
                        # This property is a sub-trait, so skip (for now)
                        # TODO: Implement sub-trait ingestion
                        continue
                    else:
                        trait_property_type = trait_schema[trait_property_name]
                    try:
                        trait_property_data = getattr(trait, trait_property_name)
                    except:
                        # Unable to retrieve the trait property for some reason. Skip for now.
                        # TODO: Provide a warning
                        tb = traceback.format_exc()
                        print(tb)
                        continue

                    if 'array' in trait_property_type:
                        # This is an array trait, so it will have to be flattened, and have it's shape stored.
                        shape = trait_property_data.shape
                        flat_list = trait_property_data.flatten().tolist()
                        # Create a java list for this python list:
                        java_list = ListConverter().convert(flat_list, gateway._gateway_client)
                        # Convert the shape to a java list as well:
                        java_shape = ListConverter().convert(shape, gateway._gateway_client)

                        # TODO: pass the java_list and java_shape to AVRO
                        # datum.put(trait_property_name, trait_property_data)
                        # traits_found_for_this_object = True
                    else: # Not an array type
                        datum.put(trait_property_name, trait_property_data)
                        traits_found_for_this_object = True

                # TODO: Implement version/branch handling here
                data_dict['b1_v1'] = datum
                java_data_map = MapConverter().convert(data_dict, gateway._gateway_client)
                astro_record.put(trait_key.trait_type, java_data_map)
            if(traits_found_for_this_object):
                # write the record out
                writer.write(astro_record)
        writer.close()
    except:
        tb = traceback.format_exc()
        print(tb)


def createSchema(schema):
    sch = '''{
                \"type\": \"record\",
                \"namespace\": \"au.gov.aao.asvo.model\",
                \"name\": \"astroObject\",
                \"fields\": [
                    {
                        \"name\": \"object_id\",
                        \"type\": \"string\"
                    },'''
    sch = doSubtraits(schema, sch, sub_trait=False)

    sch = sch[:-1] + ']}'
    return sch


def doSubtraits(value, sch, sub_trait=True):
    for k, v in value.items():
        if(isinstance(v, dict)):
            # if not sub_trait:
            #     print("Schema processing '{}' as trait.".format(k))
            # else:
            #     print("Schema processing '{}' as sub-trait.".format(k))

            sch += '''{
                        \"name\": \"''' + k + '''\",
                        \"type\": '''

            if not sub_trait:
                sch += '{\"type\": \"map\", \"values\": '

            sch += '''{
                            \"type\": \"record\",
                            \"namespace\": \"au.gov.aao.asvo.model\",
                            \"name\": \"''' + k.capitalize() + '''\",
                            \"fields\": ['''
            sch = doSubtraits(v, sch, sub_trait=True)
            if not sub_trait:
                sch += '}}},'
            else:
                sch += '}},'
        else:
            # print("Schema processing '{}' as trait property.".format(k))
            vals = v.split('.')
            if(len(vals) > 1 and vals[1] == 'array'):
                type = '{\"type\": \"array\", \"items\": \"' + vals[0] + '\"}'
            elif(len(vals) == 1):
                type = '\"' + vals[0] + '\"'
            sch += '{\"name\": \"' + k + '''\",
                    \"type\": ''' + type + '},'
    sch = sch[:-1] + ']'
    return sch


# This is an old version. Don't use this. Kept for me to experiment
def doSubtraits_V1(value, sch):
    # we know that this is a record
    for k, v in value.items():
        if(isinstance(v, dict)):
            sch += '''{
                        \"name\": \"''' + k + '''\",
                        \"type\": {\"type\": \"map\", \"values\":
                        \"type\": {
                            \"type\": \"record\",
                            \"namespace\": \"au.gov.aao.asvo.model\",
                            \"name\": \"''' + k.capitalize() + '''\",
                            \"fields\": ['''
            sch = doSubtraits(v, sch)
            sch += '}}},'
        else:
            vals = v.split('.')
            if(len(vals) > 1 and vals[1] == 'array'):
                type = '{\"type\": \"array\", \"items\": \"' + vals[0] + '\"}'
            elif(len(vals) == 1):
                type = '\"' + vals[0] + '\"'
            sch += '{\"name\": \"' + k + '''\",
                    \"type\": ''' + type + '},'
    sch = sch[:-1] + ']'
    return sch

if __name__ == '__main__':
    main()