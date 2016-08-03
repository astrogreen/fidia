import sys

from fidia.archive import example_archive, archive
from fidia.traits import Trait

from py4j.java_gateway import JavaGateway, GatewayParameters
from py4j.java_collections import MapConverter, ListConverter
import numpy as np

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
                avro_trait_schema = astro_schema.getField(trait_key.trait_type).schema()
                datum = gateway.entry_point.getDatum(avro_trait_schema.getValueType())

                # Iterate and put values
                trait_property_schema = schema[trait_key.trait_type]
                for trait_property_name in trait_property_schema:
                    if isinstance(trait_property_schema[trait_property_name], dict):
                        # This property is a sub-trait, so skip (for now)
                        # TODO: Implement sub-trait ingestion
                        continue
                    else:
                        trait_property_type = trait_property_schema[trait_property_name]
                    try:
                        trait_property_data = getattr(trait, trait_property_name).value
                    except:
                        # Unable to retrieve the trait property for some reason. Skip for now.
                        # TODO: Provide a warning
                        tb = traceback.format_exc()
                        print(tb)
                        continue

                    if 'array' in trait_property_type:
                        # This is an array trait, so it will have to be flattened, and have it's shape stored.
                        shape = trait_property_data.shape
                        # flat_list = trait_property_data.flatten().tolist()
                        # # Create a java list for this python list:
                        # java_list = ListConverter().convert(flat_list, gateway._gateway_client)

                        java_list = convert_ndarray_to_java_list(trait_property_data.flatten(), gateway)
                        # Convert the shape to a java list as well: Not required.
                        # java_shape = ListConverter().convert(shape, gateway._gateway_client)


                        # Here we need to get another record for the property.
                        # This property's avro type is a union. We need to get all the avro types of this union.
                        trait_property_union_types_schema = avro_trait_schema.getValueType().getField(trait_property_name).schema()
                        union_types_list = trait_property_union_types_schema.getTypes()
                        array_schema = union_types_list.get(1)
                        array_datum = gateway.entry_point.getDatum(array_schema)
                        array_datum.put('shape', str(shape))
                        array_datum.put('dataValues', java_list)
                        datum.put(trait_property_name, array_datum)
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
        if(k=='sub_trait'):
            continue
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
                                         {\"name\": \"dataValues\", \"type\": ''' + t + '}]}'
            elif(len(vals) == 1):
                type = '\"' + vals[0] + '\"'
            sch += '{\"name\": \"' + k + '''\",
                    \"type\": [\"null\", ''' + type + ']},'     #if null allowed, put union here ["null", type]
    sch = sch[:-1] + ']'
    return sch


def convert_ndarray_to_java_list(ndarray, gateway):

    assert isinstance(ndarray, np.ndarray)

    max_transfer_block_size = 1024**2

    def byte_array_split(byte_array, max_transfer_block_size):
        """An iterator which returns the byte array in chunks no larger than max_transfer_block_size."""
        for offset_block_index in range(len(byte_array) // max_transfer_block_size):
            offset_block_end_index = min(offset_block_index + max_transfer_block_size, len(byte_array))
            yield byte_array[offset_block_index:offset_block_end_index]


    if ndarray.dtype.type not in (np.float64, np.int32, np.int64, np.float32):
        # Type conversion will be necessary before handing to Java.
        raise NotImplementedError()

    if not ndarray.flags.c_contiguous:
        print("Warning, ndarray is not C-contigous and will have to be copied")
    ndarray_bytes = ndarray.tobytes('C')

    endianness = get_endianness(ndarray)

    #
    # Pass the byte array into Java and convert to a Java list according to type
    #
    data_type_to_java_converter_map = {
        np.float64: gateway.entry_point.doubleListFromSplitByteArray,
        np.int32: gateway.entry_point.integerListFromSplitByteArray,
        np.int64: gateway.entry_point.longListFromSplitByteArray,
        np.float32: gateway.entry_point.floatListFromSplitByteArray
    }

    java_list = data_type_to_java_converter_map[ndarray.dtype.type](
        ListConverter().convert(byte_array_split(ndarray_bytes, max_transfer_block_size), gateway._gateway_client),
        len(ndarray_bytes),
        max_transfer_block_size,
        endianness)

    return java_list

def get_endianness(ndarray):
    """Return a single character string which encodes the endianness of the ndarray for java."""
    if ndarray.dtype.byteorder == '=':
        if sys.byteorder == 'little':
            byteorder = '<'
        else:
            byteorder = '>'
    elif ndarray.dtype.byteorder == '|':
        byteorder = '>'
    else:
        byteorder = ndarray.dtype.byteorder
    return byteorder


if __name__ == '__main__':
    main()