from fidia.archive import example_archive
from fidia.archive.sami import SAMITeamArchive, SAMIDR1PublicArchive
from fidia.traits.base_traits import Trait
from fidia.utilities import SchemaDictionary
#from fidia.ingest.ingest_utility import *
import traceback

from avro.datafile import DataFileWriter
from avro.io import DatumWriter
from avro import schema
from avro import io

import time
import json
from fidia.cache.data_retriver import DataRetriever

import argparse

from avro.schema import *

#ar = example_archive.ExampleArchive()

# ar = SAMITeamArchive(
#         '/Users/lharischandra/AAO/AAT_ASVO/Data/SAMI/Django/sami_test_release',
#        '/Users/lharischandra/AAO/AAT_ASVO/Data/SAMI/Django/sami_test_release/sami_small_test_cat.fits')

# ar = SAMITeamArchive(
#         '/net/aaolxz/iscsi/data/SAMI/data_releases/v0.9/',
#         '/net/aaolxz/iscsi/data/SAMI/catalogues/sami_sel_20140911_v2.0JBupdate_July2015_incl_nonQCmet_galaxies.fits')


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
            array_dict = dict()
            if hasattr(trait_property_data[trait_property_name], 'shape'):
                # Shape attribute can provide the shape of the data (probably a
                # numpy array).
                array_dict['shape'] = str(trait_property_data[trait_property_name].shape)
                array_dict['dataValues'] = trait_property_data[trait_property_name].flatten().tolist()
            elif isinstance(trait_property_data[trait_property_name], list):
                # A one-dimensional Python list.
                array_dict['shape'] = "({})".format(len(trait_property_data[trait_property_name]))
                array_dict['dataValues'] = trait_property_data[trait_property_name]
            else:
                # Unknown array format. Skip.
                continue

            # Replace the trait_property_data with the modified, array-format version:
            trait_property_data[trait_property_name] = array_dict

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

    # Now we need to build the schema.
    # schema_string = createSchema(trait_schema)

    schema_object = get_avro_schema(trait_schema)

    #schema_object = schema.Parse(schema_string)

    field_map = schema_object.field_map

    writer = DataFileWriter(open(args.output_file, "wb"), DatumWriter(), schema_object)
    write_astro_objects(ar, trait_schema, writer)
    astro_record = dict()


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




def write_astro_objects(archive, schema, writer):
    sample = archive.get_full_sample()
    astro_obj_list = list()
    try:
        count = 0
        for object_id in sample:
            if count is 1:
                break
            astro_record = dict()
            astro_record['object_id'] = object_id
            trait_types = dict()

            for trait_type in schema:
                trait_type_schema = schema[trait_type]
                trait_type_data = dict()
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
                                versions.update({branch_version: get_property_data(trait_schema, trait_data)})
                        astro_record[trait_type] = versions
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
                    trait_type_data[type_key] = versions
                if not already_added:
                    astro_record[trait_type] = trait_type_data
            writer.append(astro_record)
            writer.flush()
            count += 1
        writer.close()
    except:
        tb = traceback.format_exc()
        print(tb)

    #return astro_obj_list

def get_property_data(schema, trait_data):
    data = dict()
    for key in schema:
        if isinstance(schema[key], SchemaDictionary):
            if trait_data['sub_trait_data'] is None:
                data[key] = None
                continue
            elif key not in trait_data['sub_trait_data']:
                data[key] = None
                continue
            sub_trait_data = trait_data['sub_trait_data'][key]['trait_property_data']
            sub_schema = schema[key]
            data[key] = get_property_data(sub_schema, sub_trait_data)
        else:
            if key not in trait_data['trait_property_data']:
                data[key] = None
            elif key is '_wcs_string':
                data[key] = 'dummy_wcs_string'
            else:
                data[key] = trait_data['trait_property_data'][key]
    return data







def get_avro_schema(schema):

    astro_record_fields = list()
    astro_record_fields.append(Field(PrimitiveSchema(STRING), 'object_id', 0, False, names=Names()))
    top_index = 0
    for trait_type in schema:                               # trait_type = line_map
        trait_type_schema = schema[trait_type]              # line_map dict. keys are - 00I0, HBeta etc.

        trait_type_avro_fields = list()
        already_added = False
        key_index = 0
        for trait_key in trait_type_schema:                 # trait_key = OII3, HBeta etc.
            trait_schema = trait_type_schema[trait_key]     # trait_schema dict

            trait_fields = list()
            field_index = 0
            for trait_property_key in trait_schema:         # comp_2_variance
                trait_prop_type = trait_schema[trait_property_key]
                if isinstance(trait_prop_type, SchemaDictionary):
                    trait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL),
                                        RecordSchema(trait_property_key.capitalize(), 'au.gov.aao.asvo.model',
                                                        get_subtraits(trait_prop_type), names=Names())]),
                                        trait_property_key, field_index, False, names=Names())

                    field_index += 1
                else:
                    dtypes = trait_prop_type.split('.')
                    if 'array' in trait_prop_type:
                        data_vals = Field(ArraySchema(PrimitiveSchema(dtypes[0])), 'dataValues', 0, False, names=Names())
                        shape = Field(PrimitiveSchema(STRING), 'shape', 1, False, names=Names())
                        trait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL),
                                            RecordSchema(trait_property_key.capitalize(), 'au.gov.aao.asvo.model',
                                            [data_vals, shape], names=Names())]), trait_property_key,
                                                 field_index, False, names=Names())

                        field_index += 1
                    else:

                        trait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(dtypes[0])]),
                                                             trait_property_key, field_index, False, names=Names())
                        field_index += 1

                trait_fields.append(trait_prop_field)

            if trait_key is None:

                astro_record_fields.append(Field(UnionSchema([PrimitiveSchema(NULL),
                                                    MapSchema(RecordSchema(trait_type.capitalize(), 'au.gov.aao.asvo.model',
                                                        trait_fields, names=Names()))]),trait_type, top_index, False, names=Names()))
                already_added = True
                top_index += 1
            else:
                trait_type_avro_fields.append(Field(UnionSchema([PrimitiveSchema(NULL),
                                                    MapSchema(RecordSchema(trait_key.capitalize(), 'au.gov.aao.asvo.model',
                                                        trait_fields, names=Names()))]), trait_key, key_index, False, names=Names()))
                already_added = False
                key_index += 1
        if not (already_added):
            astro_record_fields.append(Field(UnionSchema([PrimitiveSchema(NULL),
                                                          RecordSchema(trait_type.capitalize(), 'type_ns',
                                                                       trait_type_avro_fields, names=Names())]),
                                                                        trait_type, top_index, False, names=Names()))
            top_index += 1

    av_record_schema = RecordSchema('astroObject', 'au.gov.aao.asvo.model', astro_record_fields, names=Names())

    return av_record_schema



def get_subtraits(type):  # type = wcs dict - { None: {a: string, b: string} }

    field_list = list()

    for sub_key in type:                        # sub_key - None
        #sub_schema = StructType()
        sub_schema = list()
        field_index = 0
        sub_prop_schema = type[sub_key]         # sub_key = None.
        for k in sub_prop_schema:
            sub_prop_type = sub_prop_schema[k]
            if isinstance(sub_prop_type, SchemaDictionary):
                get_subtraits(sub_prop_type)
            else:
                sub_types = sub_prop_type.split('.')
                if 'array' in sub_prop_type:

                    data_vals = Field(ArraySchema(PrimitiveSchema(sub_types[0])), 'dataValues', 0, False)

                    shape = Field(PrimitiveSchema(STRING), 'shape', 1, False)

                    sub_prop_field = Field(UnionSchema([PrimitiveSchema(NULL),
                                            RecordSchema(k.capitalize(), 'namesp', [data_vals, shape], names=Names())]),
                                                k, field_index, False, names=Names())

                    field_index += 1
                else:
                    sub_prop_field = Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(sub_types[0])]),
                                                       k, field_index, False, names=Names())
                    field_index += 1
            sub_schema.append(sub_prop_field)

        if sub_key is None:
            return sub_schema
        else:
            #sub_trait_schema.add(sub_key, sub_schema)

            # sub_key = 4, 5, 6
            # sub_key = 4

            #{ name:4, type:record, fields:[sub_schema{name:wcs_string, type=..}, {name=bla_str, ...}]}

            # Is this a record? Yes.
            # wcs has different versions
            # we need to create a record with sub_schema fields. Then create a field from that and add it to the list

            #sub_sch_record = RecordSchema(sub_key, 'namsp', sub_schema, names=Names())

            #field_list.append(sub_sch_record)
            pass
    return field_list # should return a list of Fields


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
    parser = argparse.ArgumentParser(description='Ingest astronomical objects')
    parser.add_argument('-t', '--table', required=True, help='the impala table of the already ingested data')
    parser.add_argument('input_dir', help='input data directory')
    parser.add_argument('catalogue', help='data catalogue')
    parser.add_argument('output_file', help='the path of the avro file to write data to')
    args = parser.parse_args()

    main(args)