import sys

from fidia.archive import example_archive, archive

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

    schema_string = createSchema(schema)
    gateway = JavaGateway()
    astro_schema = gateway.entry_point.getSchema(schema_string)
    writer = gateway.entry_point.getParquetWriter(astro_schema)
    try:
        for object_id in sample:
            astro_record = gateway.entry_point.getDatum(astro_schema)
            astro_record.put("object_id", object_id)
            has_traits = False
            for trait_key in sample[object_id]:
                if(trait_key.trait_type == 'simple_heir_trait' or trait_key.trait_type == 'spectral_map'):
                    continue
                has_traits = True
                trait = sample[object_id][trait_key]
                mp = dict()

                #This needs to be a if else for nested traits
                datum = gateway.entry_point.getDatum(astro_schema.getField(trait_key.trait_type).schema().getValueType())
                # Iterate and put values
                for data_name in schema[trait_key.trait_type]:
                    try:
                        #assert isinstance(getattr(trait, data_name), np.ndarray)
                        #tt.addProperty(data_name, getattr(trait, data_name))

                        # If trait attribute is an ndarray, convert it into a java array
                        # is it possible to do that?
                        attr = getattr(trait, data_name)
                        if(isinstance(attr, ndarray)):
                            #gateway.new_array(int, 2,3) # how do I know the shape of the ndarray? have to get ndarray shape
                            attr_list = attr.tolist()
                            attr = ListConverter().convert(attr_list, gateway._gateway_client)
                        datum.put(data_name, attr)
                    except:
                        tb = traceback.format_exc()
                        print(tb)
                mp['b1_v1'] = datum
                java_mp = MapConverter().convert(mp, gateway._gateway_client)
                astro_record.put(trait_key.trait_type, java_mp)
            if(has_traits):
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
                            \"namespace\": \"au.gov.aao.asvo.model.''' + k + '''\",
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
                t = '{\"type\": \"array\", \"items\": \"' + vals[0] + '\"}' #\"namespace\": \"au.gov.aao.asvo.model.''' + k + '''\",
                type = '''{\"type\": \"record\",
                            \"name\": \"''' + k + '''NDArray\",
                            \"fields\": [{\"name\": \"shape\", \"type\": \"string\"},
                                         {\"name\": \"data\", \"type\": ''' + t + '}]}'
            elif(len(vals) == 1):
                type = '\"' + vals[0] + '\"'
            sch += '{\"name\": \"' + k + '''\",
                    \"type\": [\"null\", ''' + type + ']},'     #if null allowed, put union here ["null", type]
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