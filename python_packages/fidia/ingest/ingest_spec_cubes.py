from fidia.archive import example_archive
from fidia.archive.sami import SAMITeamArchive, SAMIDR1PublicArchive
from fidia.traits.base_traits import Trait
from fidia.utilities import SchemaDictionary
#from fidia.ingest.ingest_utility import *
from fidia.exceptions import *
import traceback

from avro.datafile import DataFileWriter
from avro.io import DatumWriter
from hdfs import InsecureClient
from hdfs.ext.avro import AvroWriter
from tempfile import TemporaryFile
from avro import schema
from avro import io

import numpy as np

import time
import json
from fidia.cache.data_retriver import DataRetriever

import argparse

from avro.schema import *

def get_traitproperty_data(trait):
    # type: (Trait) -> dict
    """Retrieve data for all trait properties attached to the Trait."""
    # Get data for TraitProperties, and store it in the following dicts.
    trait_property_type = dict()
    trait_property_data = dict()
    for trait_property_name in trait.trait_property_dir():
        trait_property_type[trait_property_name] = getattr(trait, trait_property_name).type
        try:
            trait_property_data[trait_property_name] = getattr(trait, trait_property_name).value
        except DataNotAvailable:
            # No data for this particular TraitProperty, skip.
            trait_property_type[trait_property_name] = None
            trait_property_data[trait_property_name] = None
            continue
        except:
            # Unable to retrieve the trait property for some reason. Skip for now.
            # TODO: Provide a warning
            tb = traceback.format_exc()
            print(tb)
            trait_property_type[trait_property_name] = None
            trait_property_data[trait_property_name] = None
            continue
        # Not sure what this statement achieves?
        if trait_property_data is None:
            continue
        if 'array' in trait_property_type[trait_property_name]:
            # This is an array trait, so it will have to be flattened, and have
            # it's shape stored separately.

            if hasattr(trait_property_data[trait_property_name], 'shape'):
                # Shape attribute can provide the shape of the data (probably a
                # numpy array).
                # array_dict['shape'] = str(trait_property_data[trait_property_name].shape)
                # array_dict['dataValues'] = trait_property_data[trait_property_name].flatten().tolist()
                if trait.trait_type is 'spectral_map':
                    record_fields = list()
                    sch = ""
                    shape = trait_property_data[trait_property_name].shape
                    if len(shape) is 3:
                        sch = {
                            "type": "array",
                            "items": {"type": "array",
                                      "items": {"type": "array",
                                                "items": "float"}
                                      }
                            }
                        items = ArraySchema(ArraySchema(ArraySchema(PrimitiveSchema(FLOAT))))
                    elif len(shape) is 5:
                        sch = {
                            "type": "array",
                            "items": {"type": "array",
                                      "items": {"type": "array",
                                                "items": {"type": "array",
                                                          "items": {"type": "array",
                                                                    "items": "float"}
                                                        }
                                                }
                                    }
                        }
                        items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(ArraySchema(PrimitiveSchema(FLOAT))))))
                    else:
                        print("Array size is not supported. Object id: " + trait.object_id)
                        continue

                    meta_fields = list()
                    meta_fields.append(Field(PrimitiveSchema(STRING), "object_id", 1, False))
                    meta_fields.append(Field(PrimitiveSchema(STRING), "trait_type", 2, False))
                    meta_fields.append(Field(PrimitiveSchema(STRING), "trait_qualifier", 3, False))
                    meta_fields.append(Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(STRING)]),
                                                         "branch", 4, False))
                    meta_fields.append(Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(STRING)]),
                                                         "version", 5, False))
                    meta_fields.append(Field(PrimitiveSchema(STRING), "trait_property", 6, False))
                    metadata_field = Field(RecordSchema("metadata", "trait_property", meta_fields, names=Names()),
                                           "metadata", 1, False)

                    data_field = Field(items, "data", 2, False)
                    record_schema = RecordSchema("spectral_map_property", "asvo.model.astro_object",
                                          [metadata_field, data_field], names=Names())
                    record_json = record_schema.to_json()

                    if trait.branch is None:
                        branch_version = 'No_branch'
                    else:
                        branch_version = trait.branch + '-' + trait.version
                    base_path = 'Sami_Test/Sami_Spec_Cubes_2/' + trait.object_id + '-' + trait.trait_name + '-' + branch_version
                    fname = base_path + '-' + trait_property_name + '.avro'

                    spec_record = dict()
                    meta_record = dict()

                    meta_record['object_id'] = trait.object_id
                    meta_record['trait_type'] = trait.trait_type
                    meta_record['trait_qualifier'] = trait.trait_qualifier
                    meta_record['branch'] = trait.branch
                    meta_record['version'] = trait.version
                    meta_record['trait_property'] = trait_property_name

                    spec_record['metadata'] = meta_record
                    spec_record['data'] = trait_property_data[trait_property_name]


                    with AvroWriter(get_hdfs_client(), fname, record_json, overwrite=True) as writer:
                        writer.write(spec_record)
                    # tf = TemporaryFile()
                    # np.save(tf, trait_property_data[trait_property_name])
                    # tf.seek(0)
                    # get_hdfs_client().write(fname, tf.read(), overwrite=True, encoding=None)
                    trait_property_data[trait_property_name] = fname

            elif isinstance(trait_property_data[trait_property_name], list):
                # A one-dimensional Python list.
                array_dict = dict()
                array_dict['shape'] = "({})".format(len(trait_property_data[trait_property_name]))
                array_dict['dataValues'] = trait_property_data[trait_property_name]
                trait_property_data[trait_property_name] = array_dict
            else:
                # Unknown array format. Skip.
                continue

            # Replace the trait_property_data with the modified, array-format version:
            # trait_property_data[trait_property_name] = array_dict  # this needs to be the path

    return {"trait_property_types": trait_property_type,
            "trait_property_data": trait_property_data}


def get_sub_trait_data(trait):
    # type: (Trait) -> dict
    """Retrieve data for sub-Traits attached to the Trait"""
    # Iterate through sub_traits by recursing on this function.
    #
    # NOTE: There are two versions of the code below, one of which is
    # commented out. Version 1 supports branches/versions in sub-traits,
    # while version 2 does not.

    # Place to store the sub_trait data:
    sub_trait_data = dict()
    for sub_trait_name in trait.sub_traits.get_trait_names():
        # ------ VERSION 1 ------
        # This version of the code is designed for if sub-traits
        # have branches and versions. This is not currently supported.
        #
        # for traitkey in trait.sub_traits.get_all_traitkeys():
        #     sub_trait_data[sub_trait_name] = dict()
        #     # Only include traits in this loop which have the right trait_name:
        #     if traitkey.trait_name == sub_trait_name:
        #         sub_trait_branch_version = traitkey.branch + "-" + traitkey.version
        #         sub_trait = trait.sub_traits.retrieve_with_key(traitkey)
        #         sub_trait_data[sub_trait_name][sub_trait_branch_version] = get_trait_data(sub_trait)

        # ------ VERSION 2 ------
        # This version is for non-versioned sub-traits. In this case,
        # there is no version or branches, so the trait_name will
        # uniquely identify the trait.
        #
        # Note that this will not break even if the archive actually
        # has branched and versioned sub-traits, but only the default
        # will be made available here.

        sub_trait = trait.sub_traits.retrieve_with_key(sub_trait_name)
        sub_trait_data[sub_trait_name] = get_trait_data(sub_trait)

def get_trait_data(trait):
    # type: (Trait) -> dict
    """Retrieve data for TraitProperties and sub-Traits attached to the Trait"""

    result = dict()

    # Get data for TraitProperties
    trait_property_data = get_traitproperty_data(trait)
    # Add TraitProperty data to result
    result.update(trait_property_data)

    # Get data for sub-Traits
    sub_trait_data = get_sub_trait_data(trait)
    # Add sub_trait_data to result
    result.update({"sub_trait_data": sub_trait_data})

    return result


def main(args):

    #ar = SAMITeamArchive(args.input_dir, args.catalogue)
    ar = SAMIDR1PublicArchive(args.input_dir, args.catalogue)

    trait_schema = ar.schema()

    schema_object = get_avro_schema(trait_schema)

    #schema_object = schema.Parse(schema_string)

    writer = DataFileWriter(open(args.output_file, "wb"), DatumWriter(), schema_object)
    startTime = time.clock()
    write_astro_objects(ar, trait_schema, writer)
    endTime = time.clock()
    print('Time to ingest 3 Objects is ' + str(endTime - startTime))


def removeIngestedObjects(sample, table):
    """
    Remove already ingested objects ids from the sample and return the
    list of remaining item ids
    """

    # get a list of already ingested object ids from impala
    obj_ids = DataRetriever().sql("Select object_id from " + table)
    obj_id_list = list()
    for obj in obj_ids:
        obj_id_list.append(obj[0])

    remaining_ids = set(sample.keys()).difference(set(obj_id_list))
    print('Remaining ids:\n' + str(remaining_ids))
    return remaining_ids

def get_hdfs_client():
    client = InsecureClient("http://asvotest1.aao.gov.au:50070", 'lharischandra')
    return client


def write_astro_objects(archive, schema, writer):
    sample = archive.get_full_sample()
    astro_obj_list = list()
    try:
        count = 0
        for object_id in sample:
            # if count is 3:
            #     break
            astro_record = dict()
            astro_record['object_id'] = object_id
            trait_types = dict()

            for trait_type in schema:
                if not trait_type is "spectral_map":
                    continue
                trait_type_schema = schema[trait_type]

                trait_type_data = dict()
                already_added = False


                for trait_qualifier in trait_type_schema:        # trait_qualifier = HBeta, 00II3
                    trait_schema = trait_type_schema[trait_qualifier]

                    # get the trait for the key
                    versions = dict()
                    if trait_qualifier is None:
                        # This is a map at this level

                        for trait_key in archive.available_traits.get_all_traitkeys(trait_name_filter=trait_type):
                            try:
                                trait = sample[object_id][trait_key]
                            except DataNotAvailable:
                                continue
                            if trait.branch is None:
                                branch_version = 'No_branch'
                            else:
                                branch_version = trait.branch + '-' + trait.version
                            trait_data = get_trait_data(trait)
                            versions.update({branch_version: get_record_data(trait_schema, trait_data)})
                        astro_record[trait_type] = versions
                        already_added = True
                    else:
                        # This is a map that needs to be added to trait_type record
                        for trait_key in archive.available_traits.get_all_traitkeys(trait_name_filter=trait_type + '-' + trait_qualifier):
                            try:
                                trait = sample[object_id][trait_key]   # what happens if there are more than 1 version?
                            except DataNotAvailable:
                                continue
                            if trait.branch is None:
                                branch_version = 'No_branch'
                            else:
                                branch_version = trait.branch + '-' + trait.version
                            trait_data = get_trait_data(trait)
                            versions.update({branch_version: get_record_data(trait_schema, trait_data)})
                    trait_type_data[trait_qualifier] = versions
                if not already_added:
                    astro_record[trait_type] = trait_type_data
            writer.append(astro_record)
            writer.flush()
            count += 1
        writer.close()
        print(str(count) + " objects ingested.")
    except:
        tb = traceback.format_exc()
        print(tb)

        #return astro_obj_list

def get_record_data(schema, trait_data):
    data = dict()
    for key in schema:
        if isinstance(schema[key], SchemaDictionary):
            if trait_data['sub_trait_data'] is None:
                data[key] = None
                continue
            elif key not in trait_data['sub_trait_data']:
                data[key] = None
                continue
            sub_records = dict()
            already_added = False
            sub_trait_data = trait_data['sub_trait_data'][key]#['trait_property_data']
            for sub_key in schema[key]:
                sub_record = get_record_data(schema[key][sub_key], sub_trait_data)
                if sub_key is None:
                    data[key] = sub_record
                    already_added = True
                else:
                    sub_records[sub_key] = sub_record
            if not already_added:
                data[key] = sub_records
        else:
            if key not in trait_data['trait_property_data']:
                data[key] = None
            elif key is '_wcs_string':
                data[key] = str(trait_data['trait_property_data'][key].ascard)
            else:
                data[key] = trait_data['trait_property_data'][key]
    return data



def get_avro_schema(schema):
    astro_record_fields = list()
    astro_record_fields.append(Field(PrimitiveSchema(STRING), 'object_id', 0, False))
    field_index = 1
    for trait_type in schema:
        if not trait_type is 'spectral_map':
            continue
        trait_type_schema = schema[trait_type]
        trait_type_field = process_trait_type_schema(trait_type_schema, trait_type, field_index, 'asvo.model', True)
        astro_record_fields.append(trait_type_field)
        field_index += 1

    return RecordSchema('astroObject', 'asvo.model', astro_record_fields, names=Names())


def process_trait_type_schema(schema_dict, trait_type, index, namespace_prefix,
                              include_branch_version=False):
    key_fields = list()
    key_index = 0
    for key in schema_dict:

        if key is None:
            values = create_avro_record(schema_dict[key], trait_type, namespace_prefix + "." + trait_type)
            if include_branch_version:
                key_field = Field(UnionSchema([PrimitiveSchema(NULL), MapSchema(values)]), trait_type, index, False)
            else:
                key_field = Field(UnionSchema([PrimitiveSchema(NULL), values]), trait_type, index, False)
            return key_field
        else:
            values = create_avro_record(schema_dict[key], key,
                                        namespace_prefix + "." + trait_type + '.' + key)
            if include_branch_version:
                key_field = Field(UnionSchema([PrimitiveSchema(NULL), MapSchema(values)]), key, key_index, False)
            else:
                key_field = Field(UnionSchema([PrimitiveSchema(NULL), values]), key, key_index, False)

            key_fields.append(key_field)
            key_index += 1

    return Field(RecordSchema(trait_type.capitalize(), namespace_prefix + '.' + trait_type,
                              key_fields, names=Names()), trait_type, index, False)


def create_avro_record(trait_schema, name, namespace):

    trait_fields = list()
    field_index = 0
    for trait_prop_key in trait_schema:         # comp_2_variance
        trait_prop_type = trait_schema[trait_prop_key]
        if isinstance(trait_prop_type, SchemaDictionary):
            trait_type_field = process_trait_type_schema(trait_prop_type, trait_prop_key, field_index, namespace)
            trait_fields.append(trait_type_field)
        else:
            dtypes = trait_prop_type.split('.')
            if 'array' in trait_prop_type:
                if trait_prop_key is 'source_rss_frames':
                    data_vals = Field(ArraySchema(PrimitiveSchema(dtypes[0])), 'dataValues', 0, False)
                    shape = Field(PrimitiveSchema(STRING), 'shape', 1, False)
                    trait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL), RecordSchema(trait_prop_key.capitalize(),
                                                                namespace + "." + trait_prop_key, [data_vals, shape],
                                                                names=Names())]),
                                             trait_prop_key, field_index, False)
                    trait_fields.append(trait_prop_field)
                else:
                    trait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(STRING)]),
                                             trait_prop_key, field_index, False)
                    trait_fields.append(trait_prop_field)
            else:
                trait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(dtypes[0])]),
                                         trait_prop_key, field_index, False)
                trait_fields.append(trait_prop_field)
        field_index += 1

    return RecordSchema(name.capitalize(), namespace, trait_fields, names=Names())



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest astronomical objects')
    parser.add_argument('-t', '--table', required=True, help='the impala table of the already ingested data')
    parser.add_argument('input_dir', help='input data directory')
    parser.add_argument('catalogue', help='data catalogue')
    parser.add_argument('output_file', help='the path of the avro file to write data to')
    args = parser.parse_args()

    main(args)