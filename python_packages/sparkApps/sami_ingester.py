import traceback

from fidia.traits import Trait
from pyspark import SparkConf, SparkContext, SQLContext
from pyspark.sql.types import *
from pyspark.sql import types
from fidia.archive.sami import SAMITeamArchive, SAMIDR1PublicArchive
from fidia.utilities import SchemaDictionary
from fidia.ingest.ingest_utility import *
import argparse
import os

#os.environ["PYSPARK_PYTHON"] = '/usr/local/bin/python3'

def main(args):

    ar = SAMIDR1PublicArchive(args.input_dir, args.catalogue)
    conf = SparkConf().setAppName('sami_ingester')
    sc = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)


    avro_schema = get_avro_schema(ar.schema())
    rdd_obj_list = getAstroObjects(ar, ar.schema())

    astroRDD = sc.parallelize(rdd_obj_list, args.num_partitions)
    astroDF = sqlContext.createDataFrame(astroRDD, avro_schema)

    astroDF.write.parquet(args.output_file) #args.output_file


def get_avro_schema(schema):

    avro_record_schema = StructType()
    avro_record_schema.add('object_id', StringType(), False)

    for trait_type in schema:                               # trait_type = line_map
        trait_type_schema = schema[trait_type]              # line_map dict. keys are - 00I0, HBeta etc.

        trait_type_avro_schema = StructType()
        already_added = False

        for trait_key in trait_type_schema:                 # trait_key = OII3, HBeta etc.
            trait_schema = trait_type_schema[trait_key]     # trait_schema dict
            trait_avro_schema = StructType()
            for trait_property_key in trait_schema:         # comp_2_variance
                trait_prop_type = trait_schema[trait_property_key]
                if isinstance(trait_prop_type, SchemaDictionary):
                    trait_prop_field = StructField(trait_property_key, get_subtraits(trait_prop_type))
                else:
                    dtypes = trait_prop_type.split('.')
                    if 'array' in trait_prop_type:
                        array_type = StructType()
                        array_type.add('dataValues', ArrayType(get_spark_type(dtypes[0])))
                        array_type.add('shape', StringType(), False)
                        trait_prop_field = StructField(trait_property_key, array_type)
                    else:
                        trait_prop_field = StructField(trait_property_key, get_spark_type(dtypes[0]))
                trait_avro_schema.add(trait_prop_field)
            if trait_key is None:
                avro_record_schema.add(trait_type, MapType(StringType(), trait_avro_schema))
                already_added = True
            else:
                trait_type_avro_schema.add(trait_key, MapType(StringType(), trait_avro_schema))
                already_added = False
        if not (already_added):
            avro_record_schema.add(trait_type, trait_type_avro_schema)

    return avro_record_schema


def get_subtraits(type):
    sub_trait_schema = StructType()
    for sub_key in type:                        # sub_key - None
        sub_schema = StructType()
        sub_prop_schema = type[sub_key]         # this is a dict.
        for k in sub_prop_schema:
            sub_prop_type = sub_prop_schema[k]
            if isinstance(sub_prop_type, SchemaDictionary):
                get_subtraits(sub_prop_type)
            else:
                sub_types = sub_prop_type.split('.')
                if 'array' in sub_prop_type:
                    array_type = StructType()
                    array_type.add('dataValues', ArrayType(get_spark_type(sub_types[0])))
                    array_type.add('shape', StringType(), False)
                    sub_prop_field = StructField(k, array_type)
                else:
                    sub_prop_field = StructField(k, get_spark_type(sub_types[0]))
            sub_schema.add(sub_prop_field)
        if sub_key is None:
            return sub_schema
        else:
            sub_trait_schema.add(sub_key, sub_schema)

    return sub_schema


def getAstroObjects(archive, schema):

    sample = archive.get_full_sample()
    astro_obj_list = list()
    try:
        count = 0
        for object_id in sample:
            if count is 2:
                break
            astro_record = list()
            astro_record.append(object_id)
            trait_types = dict()

            for trait_type in schema:
                trait_type_schema = schema[trait_type]
                trait_type_data = list()
                already_added = False
                for type_key in trait_type_schema:        # type_key = HBeta, 00II3
                    trait_schema = trait_type_schema[type_key]

                    # get the trait for the key
                    versions = dict()
                    if type_key is None:
                        for trait_key in sample[object_id].keys():
                            if trait_type in trait_key.trait_name:
                                trait = sample[object_id][trait_key]
                                if trait.branch is None:
                                    branch_version = None
                                else:
                                    branch_version = trait.branch + '-' + trait.version
                                trait_data = get_trait_data(trait)
                                # trait_prop_data = list()
                                # for trait_property_name in trait_schema:
                                #     if isinstance(trait_schema[trait_property_name], dict):
                                #         # This property is a sub-trait, so skip (for now)
                                #         sub_data = list()
                                #         # if trait_data['sub_trait_data'] is None:
                                #         #     trait_prop_data.append(None)
                                #         #     continue
                                #         if trait_data['sub_trait_data'] is None or \
                                #                         trait_property_name not in trait_data['sub_trait_data']:
                                #             trait_prop_data.append(None)
                                #             continue
                                #         sub_trait = trait_data['sub_trait_data'][trait_property_name]
                                #         # iterate over sub props
                                #         sub_data.append()
                                #         data = trait_data['sub_trait_data'][trait_property_name]
                                #     else:
                                #         if trait_property_name not in trait_data['trait_property_data']:
                                #             trait_prop_data.append(None)
                                #             continue
                                #         data = trait_data['trait_property_data'][trait_property_name]
                                #         trait_prop_data.append(data)

                                versions.update({branch_version: get_property_data(trait_schema, trait_data)})
                        astro_record.append(versions)
                        already_added = True
                    else:
                        #for trait_key in archive.available_traits.get_all_traitkeys(trait_name_filter=trait_type + '-' + type_key):
                        for trait_key in sample[object_id].keys():
                            if trait_type + '-' + type_key in trait_key.trait_name:
                                trait = sample[object_id][trait_key]   # what happens if there are more than 1 version?
                                if trait.branch is None:
                                    branch_version = None
                                else:
                                    branch_version = trait.branch + '-' + trait.version
                                trait_data = get_trait_data(trait)
                                versions.update({branch_version: get_property_data(trait_schema, trait_data)})
                                #
                                # trait_prop_data = list()
                                # for trait_property_name in trait_schema:
                                #     if isinstance(trait_schema[trait_property_name], dict):
                                #         trait_prop_data.append(get_subtrait_data(sub_schema, sub_prop_data))
                                #
                                #         for sub_key in sub_schema:
                                #             if isinstance(sub_schema[sub_key], dict()):
                                #                 get_subtrait_data()
                                #             else:
                                #                 if sub_key not in sub_prop_data['trait_property_data']:
                                #                     sub_data.append(None)
                                #                     continue
                                #                 sub_data.append(sub_prop_data['trait_property_data'][sub_key])
                                #         trait_prop_data.append(get_subtrait_data(trait_schema[trait_property_name]),
                                #                                trait_data['sub_trait_data'])
                                #     else:
                                #         if trait_property_name not in trait_data['trait_property_data']:
                                #             trait_prop_data.append(None)
                                #             continue
                                #         data = trait_data['trait_property_data'][trait_property_name]
                                #         # this is a single value. This should be added to a list
                                #         trait_prop_data.append(data)
                                #
                                #
                                #
                                # versions.update({branch_version: trait_prop_data})
                    trait_type_data.append(versions)
                if not already_added:
                    astro_record.append(trait_type_data)
            astro_obj_list.append(astro_record)
            count += 1

    except:
        tb = traceback.format_exc()
        print(tb)

    return astro_obj_list

def get_property_data(schema, trait_data):
    data = list()
    for key in schema:
        if isinstance(schema[key], SchemaDictionary):
            if trait_data['sub_trait_data'] is None:
                data.append(None)
                continue
            elif key not in trait_data['sub_trait_data']:
                data.append(None)
                continue
            sub_trait_data = trait_data['sub_trait_data'][key]['trait_property_data']
            sub_schema = schema[key]
            data.append(get_property_data(sub_schema, sub_trait_data))
        else:
            if key not in trait_data['trait_property_data']:
                data.append(None)
            elif key is '_wcs_string':
                data.append('dummy_wcs_string')
            else:
                data.append(trait_data['trait_property_data'][key])
    return data

def get_spark_type(type):
    return {
        'boolean': BooleanType(),
        'int': IntegerType(),
        'float': FloatType(),
        'double': DoubleType(),
        'string': StringType()
    }[type]



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest astronomical objects')
    #parser.add_argument('-t', '--table', required=True, help='the impala table of the already ingested data')
    parser.add_argument('input_dir', help='input data directory')
    parser.add_argument('catalogue', help='data catalogue')
    parser.add_argument('output_file', help='the path of the parquet file to write data to')
    parser.add_argument('num_partitions', help='number of partitions')
    args = parser.parse_args()

    main(args)
