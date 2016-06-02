from fidia.archive import example_archive
from fidia.archive.sami import SAMITeamArchive
from fidia.traits.base_traits import Trait

import traceback

from avro.datafile import DataFileWriter
from avro.io import DatumWriter
from avro import schema
from avro import io

from avro.schema import RECORD

#ar = example_archive.ExampleArchive()

ar = SAMITeamArchive(
        '/Users/lharischandra/AAO/AAT_ASVO/Data/SAMI/Django/sami_test_release',
       '/Users/lharischandra/AAO/AAT_ASVO/Data/SAMI/Django/sami_test_release/sami_small_test_cat.fits')

def main():
    trait_schema = ar.schema()

    # Now we need to build the schema.
    schema_string = createSchema(trait_schema)
    schema_object = schema.Parse(schema_string)

    field_map = schema_object.field_map

    # TODO: parameterize the file path
    writer = DataFileWriter(open("astro_test6.avro", "wb"), DatumWriter(), schema_object)
    astro_record = dict()
    sample = ar.get_full_sample()
    try:
        for object_id in sample:
            astro_record['object_id'] = object_id

            for trait_key in sample[object_id]:

                assert trait_key.trait_type in trait_schema
                trait = sample[object_id][trait_key]
                assert isinstance(trait, Trait)
                trait_map = dict()
                trait_record = dict()
                trait_avro_schema = field_map[trait_key.trait_type]
                print(trait_avro_schema)
                if isinstance(trait_avro_schema.type, schema.MapSchema): # This check is not a necessity
                    version = 'b1_v1'
                    #record_schema = trait_avro_schema.type.values
                    #record_fields = record_schema.field_map

                    trait_property_schema = trait_schema[trait_key.trait_type]
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
                            if trait_property_data is None:
                                continue
                            data_dict = dict()
                            if 'string' in trait_property_type:
                                data_dict['shape'] = '(1,0)'
                                data_dict['dataValues'] = trait_property_data
                            else:
                                data_dict['shape'] = str(trait_property_data.shape)
                                data_dict['dataValues'] = trait_property_data.flatten().tolist()
                            trait_record[trait_property_name] = data_dict
                        else:
                            trait_record[trait_property_name] = trait_property_data
                    trait_map[version] = trait_record
                    astro_record[trait_key.trait_type] = trait_map

            writer.append(astro_record)
            writer.flush()
        writer.close()
    except:
        tb = traceback.format_exc()
        print(tb)


    # writer = DataFileWriter(open("users.avro", "wb"), DatumWriter(), schema)
    # writer.append({"name": "Alyssa", "favorite_number": 256})
    # writer.append({"name": "Ben", "favorite_number": 7, "favorite_color": "red"})
    # writer.close()
    #
    # array_sch = schema.ArraySchema()


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

if __name__ == '__main__':
    main()