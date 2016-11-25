from fidia.archive import example_archive
from fidia.archive.sami import SAMITeamArchive, SAMIDR1PublicArchive
from fidia.traits.base_trait import Trait
from fidia.utilities import SchemaDictionary
from fidia.ingest.ingest_utility import *
from fidia.exceptions import *
import traceback

from hdfs import InsecureClient
from hdfs.ext.avro import AvroWriter
from avro.datafile import DataFileWriter
from avro.io import DatumWriter
from avro import schema
from avro import io

import time
import json

import argparse

from avro.schema import *


def main(args):
    ar = SAMIDR1PublicArchive(args.input_dir, args.catalogue)
    #write_astro_objects(ar)
    #create_tables(ar)
    schema_object = create_avro_schema(ar)
    create_astro_object(ar, schema_object, args.output_file)


def create_avro_schema(archive):
    """
    The key to this method is process the schema level by level. i.e. trait type, type-qualifier,
    branch-versions and properties. Then add each field to the astro_record.

    We need to go to the lowest level that is versions to get trait properties. These will be the fields of the
    trait properties record. In other words the the properties of the branch_version column.

    branch_version fields will be the fields of the trait_type-trait_qualifer Record. trait_type-trait_qualifier fields
    are fields of astro_object_record
    :param archive:
    :return:
    """
    schema = archive.full_schema()

    # First, object_id field
    astro_record_fields = list()
    astro_record_fields.append(Field(PrimitiveSchema(STRING), 'object_id', 0, False))

    # Now we have separated sub traits from traits. So we know what are subtraits and what are traits
    schema = archive.full_schema()
    sample = archive.get_full_sample()
    namespace_prefix = 'asvo.model.db'
    try:
        # Iterate over the schema
        type_index = 0
        for trait_type in schema:
            # if type_index is 3:
            #     break
            trait_type_schema = schema[trait_type]
            type_prefix = namespace_prefix + '.' + trait_type
            qualifier_index = 0
            qualifier_records = list()
            already_added = False
            for trait_qualifier in trait_type_schema:        # trait_qualifier = HBeta, 00II3
                trait_schema = trait_type_schema[trait_qualifier]
                if trait_qualifier is None:
                    qualifier_prefix = type_prefix
                    # Trait qualifier is None. So record name is trait name. This is the only record we have.
                    # Type of the qualifier field needs to be a map to avoid avro naming violations
                    # keys are branch names. Values is of Record type and fields of it are version records.
                    # Get the branch records
                    branch_records = add_branch_and_version_records(trait_schema, qualifier_prefix)
                    qualifier_field = Field(RecordSchema(trait_type.capitalize(), qualifier_prefix.lower(),
                                                         branch_records, names=Names()), trait_type, type_index, False)

                    # qualifier_field = Field(MapSchema(RecordSchema('branch', qualifier_prefix, version_fields, names=Names())),
                    #                         trait_type, type_index, False)

                    # Add the qualifier_field to trait_type_records
                    astro_record_fields.append(qualifier_field)
                    type_index += 1
                    already_added = True
                else:
                    qualifier_prefix = type_prefix + '.' + trait_qualifier

                    branch_records = add_branch_and_version_records(trait_schema, qualifier_prefix)
                    qualifier_field = Field(RecordSchema(trait_qualifier.capitalize(), qualifier_prefix.lower(),
                                                branch_records, names=Names()), trait_qualifier, qualifier_index, False)
                    qualifier_records.append(qualifier_field)
                    qualifier_index += 1
            if not already_added:
                # Add the qualifier_records to trait_type_field
                type_field = Field(RecordSchema(trait_type.capitalize(), type_prefix.lower(), qualifier_records, names=Names()),
                                   trait_type, type_index, False)
                astro_record_fields.append(type_field)
                type_index += 1
    except:
        print(traceback.format_exc())

    print("Writing complete.")
    return RecordSchema("astronomical_object", namespace_prefix, astro_record_fields, names=Names())

def add_branch_and_version_records(trait_schema, qualifier_prefix):
    branch_records = list()
    branch_index = 0
    for branch in trait_schema:
        versions = trait_schema[branch]
        version_records = list()
        version_index = 0
        #TODO Prepend branch name with "b_" so it complies with AVRO naming standards. May change.
        branch = "b_" + branch
        branch_prefix = qualifier_prefix + '.' + branch

        # Branch is the key of the Map. Values of the Map is of Record type.
        # Record fields per branch are the version numbers. Types of those version numbers are Records

        for version in versions:
            version_prefix = branch_prefix + '.' + version

            trait_fields = make_trait_property_fields(versions[version], version_prefix)
            # Add it to record
            version_field = Field(RecordSchema(version.capitalize(), version_prefix.lower(), trait_fields, names=Names()),
                                  version, version_index, False)
            version_records.append(version_field)
            version_index += 1
        branch_field = Field(RecordSchema(branch.capitalize(), branch_prefix.lower(), version_records, names=Names()),
                             branch, branch_index, False)
        branch_records.append(branch_field)
        branch_index += 1
    return branch_records


def make_trait_property_fields(version, namespace_prefix):
    trait_properties = version['trait_properties']
    subtrait_properties = version['sub_traits']
    prop_index = 0
    prop_fields = list()
    for property in trait_properties:
        # col_type += trait_properties[property]['name'] + ' ' + \
        #             trait_properties[property]['type'] + ','

        name = trait_properties[property]['name']
        type = trait_properties[property]['type']

        if 'array' in type:
            dtypes = type.split('.')

            if dtypes[2] is '1':
                items = ArraySchema(PrimitiveSchema(dtypes[0]))
            elif dtypes[2] is '2':
                items = ArraySchema(ArraySchema(PrimitiveSchema(dtypes[0])))
            elif dtypes[2] is '3':
                items = ArraySchema(ArraySchema(ArraySchema(PrimitiveSchema(dtypes[0]))))
            elif dtypes[2] is '4':
                items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(PrimitiveSchema(dtypes[0])))))
            elif dtypes[2] is '5':
                items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(ArraySchema(
                        PrimitiveSchema(dtypes[0]))))))
            elif dtypes[2] is '6':
                items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(ArraySchema(
                        ArraySchema(PrimitiveSchema(dtypes[0])))))))
            else:
                print("Array size is not supported. Size : ")
                continue

            property_field = Field(UnionSchema([PrimitiveSchema(NULL), items]), name,
                                   prop_index, False)
            prop_fields.append(property_field)
        else:
            property_field = Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(type)]), name,
                                   prop_index, False)
            prop_fields.append(property_field)

        prop_index += 1

    #process subtrait properties.
    for key in subtrait_properties:
        #key is the name of the field. Field type is record
        subtrait_fields = make_trait_property_fields(subtrait_properties[key][None], namespace_prefix + '.' + key)

        subtrait_prop_field = Field(UnionSchema([PrimitiveSchema(NULL), RecordSchema(key.capitalize(),
                                    (namespace_prefix + '.' + key).lower(), subtrait_fields, names=Names())]),
                                    key, prop_index, False)
        prop_fields.append(subtrait_prop_field)
        prop_index += 1
    return prop_fields

def create_astro_object(archive, schema_object, path_prefix):
    """
    Create the astro object according to AVRO schema. It is a dictionary with keys like object_id, trait_type etc.
    trait_type is also a dictionary containing either trait_qualifiers or branches.
    :param archive:
    :return:
    """
    sample = archive.get_full_sample()
    schema = archive.schema()
    astro_obj_list = list()
    try:
        count = 0
        for object_id in sample:
            if count is 3:
                break

            # writer = DataFileWriter(open(path_prefix + object_id + '.avro', "wb"), DatumWriter(), schema_object)
            astro_record = dict()
            astro_record['object_id'] = object_id

            for trait_type in schema_object.field_map:
                # key is trait_type
                trait_field = schema_object.field_map[trait_type]
                trait_type_data = dict()
                if not isinstance(trait_field.type, RecordSchema):
                    continue
                for key in trait_field.type.field_map:
                    # key either be trait_qualifier or branch name
                    key_field = trait_field.type.field_map[key]
                    if key.startswith("b_"):
                        #branch
                        branch = key.replace("b_", "", 1)
                        branch_data = dict()
                        # Need to find the version.
                        for version in key_field.type.field_map:
                            try:
                                trait = sample[object_id]["{0}:{1}({2})".format(trait_type, branch, version)]
                                # Now get the trait property data
                                version_data = get_trait_data(trait)
                                branch_data[version] = version_data

                                # data has 3 keys: trait_property_types, trait_property_data and sub_trait_data
                                # we need to update version_data dictionary with trait_property_data + sub_trait_data.
                                # trait_property_data
                                # version_data = dict()
                                # version_data.update(data['trait_property_data'])
                                # for k in data['sub_trait_data']:
                                #     sub_trait_data = data['sub_trait_data'][k]
                                #     version_data.update(sub_trait_data['trait_property_data'])
                                # Can we find how deep do sub_traits go? as in how many levels are there
                            except DataNotAvailable:
                                continue
                        trait_type_data["b_" + branch] = branch_data
                    else:
                        # key is the qualifier. Now has to find the branch and version
                        qualifier_data = dict()
                        for branch in key_field.type.field_map:
                            branch_field = key_field.type.field_map[branch]
                            branch = branch.replace("b_", "", 1)
                            branch_data = dict()
                            for version in branch_field.type.field_map:
                                try:
                                    trait = sample[object_id]["{0}-{1}:{2}({3})".format(trait_type, key, branch, version)]
                                    # Now get the trait property data
                                    version_data = get_trait_data(trait)
                                    branch_data[version] = version_data

                                    # version_data = dict()
                                    # version_data.update(data['trait_property_data'])
                                    # for k in data['sub_trait_data']:
                                    #     sub_trait_data = data['sub_trait_data'][k]
                                    #     version_data.update(sub_trait_data['trait_property_data'])
                                except DataNotAvailable:
                                    continue
                            qualifier_data["b_" + branch] = branch_data
                        trait_type_data[key] = qualifier_data
                astro_record[trait_type] = trait_type_data
            with AvroWriter(get_hdfs_client(), path_prefix + object_id + '.avro', schema_object.to_json(),
                            overwrite=True) as writer:
                writer.write(astro_record)
            # writer.append(astro_record)
            # writer.flush()
            # writer.close()
            count += 1
        print(str(count) + " objects ingested.")
    except:
        tb = traceback.format_exc()
        print(tb)

def get_branch_records(trait_schema):
    # create branch_records
    for branch in trait_schema:
        pass

def make_branch_maps(trait_schema, namespace_prefix):
    """

    :param trait_schema:
    :param namespace_prefix: this should be prefix + trait_type[ + trait_qualifier]
    :return:
    """
    # Branch is the key of the Map. Values of the Map is of Record type.
    # Record fields per branch are the version numbers. Types of those version numbers are Records
    for branch in trait_schema:
        map_key = branch
        b_name = 'b_' + branch
        versions = trait_schema[branch]
        version_fields = list()
        version_index = 0
        for version in versions:
            # version_prefix = branch_prefix + '.' + version

            trait_fields = make_trait_property_fields(versions[version], version_prefix)
            # Add it to record
            version_field = Field(RecordSchema(version.capitalize(), version_prefix.lower(), trait_fields, names=Names()),
                                  version, version_index, False)
            version_fields.append(version_field)
            version_index += 1

        map_values = RecordSchema(b_name, 'asvo.model.db.trait_type' + b_name, version_fields, names=Names())
        # Now we have map_key and map_values schema. Key is not important. Key is only added when the map is populated.
        # So all the values in the map should conform to the above map_values Record. Therefore trait_type's avro type
        # has to be a record. Each field of the record is a Map

def get_hdfs_client():
    client = InsecureClient("http://asvotest1.aao.gov.au:50070", 'lharischandra')
    return client

def handleSubTraits(subtraits, col_type):
    for key in subtraits:
        col_type += key + ' struct<'
        trait_properties = subtraits[key][None]['trait_properties']
        for property in trait_properties:
            # name = property['name']
            # type = property['type']
            col_type += trait_properties[property]['name'] + ' ' + \
                        trait_properties[property]['type'] + ','

        #If there are subtraits, we need to handle them as well
        #if not subtraits[key][None]['sub_traits'] is None:
        handleSubTraits(subtraits[key][None]['sub_traits'], col_type)
        #else:
        col_type = col_type[:-1] + '>,'
    return col_type


def get_trait_type_qualifier_field(schema, name, namespace):
    """

    :param schema:
    :param name:
    :param namespace:
    :return:
    """

    # Now generate fields for the record. Do they need to be branches or branch-versions?
    version_fields = list()
    for branch in schema:
        versions = schema[branch]
        for version in versions:
            branch_version = branch + '-' + version # name of the field
            col_type = 'struct<'

            # Now get the fields for this record
            fields = create_trait_fields()
            version_field = Field(RecordSchema(branch_version, namespace + '.' + branch_version, fields))
            version_fields.append(version_field)


            trait_properties = versions[version]['trait_properties']
            for property in trait_properties:
                # name = property['name']
                # type = property['type']
                col_type += trait_properties[property]['name'] + ' ' + \
                            trait_properties[property]['type'] + ','

            #If there are subtraits, we need to handle them as well
            #if not len(versions[version]['sub_traits']) is 0:
            col_type = handleSubTraits(versions[version]['sub_traits'], col_type)
            col_type = col_type[:-1] + '>'
            create_query += branch_version + ' ' + col_type + ','
            #create_query += column_defs + ','
    create_query = create_query[:-1] + ')'

    return RecordSchema(name, namespace, version_fields)



def write_astro_objects(archive):
    """
       Write one file per object. Create AVRO schema for that particular object.

    :param archive:
    :return:
    """
    schema_object = ''
    writer = DataFileWriter(open(args.output_file, "wb"), DatumWriter(), schema_object) # This needs to go into the loop
    startTime = time.clock()
    endTime = time.clock()
    print('Time to ingest 3 Objects is ' + str(endTime - startTime))

    schema = archive.schema()
    sample = archive.get_full_sample()
    astro_obj_list = list()
    try:
        count = 0
        for object_id in sample:
            if count is 3:
                break
            astro_record = dict()
            astro_record['object_id'] = object_id
            trait_types = dict()

            for trait_type in schema:
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
                                # trait_data = get_trait_data(trait)
                                # versions.update({branch_version: get_record_data(trait_schema, trait_data)})
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
                                # trait_data = get_trait_data(trait)
                                # versions.update({branch_version: get_record_data(trait_schema, trait_data)})
                    trait_type_data[trait_qualifier] = versions
                if not already_added:
                    astro_record[trait_type] = trait_type_data
            writer.append(astro_record)
            writer.flush()
            count += 1
        writer.close()
    except:
        tb = traceback.format_exc()
        print(tb)





























def create_tables(archive):
    """
        Iterate over all the objects and insert into separate tables. First object will tell you the dimensions of the
    Array types in trait properties. They are same for all objects for that particular trait type.

    :param archive:
    :return:
    """
    # First create the tables using the first astro object.
    schema = archive.full_schema()
    sample = archive.get_full_sample()

    try:
        for object_id in sample:
            astroObj = sample[object_id]

            # Iterate over the schema
            for trait_type in schema:
                trait_type_schema = schema[trait_type]

                trait_type_data = dict()
                already_added = False
                #table_name = 'hive.sami_test.' + trait_type
                for trait_qualifier in trait_type_schema:        # trait_qualifier = HBeta, 00II3

                    trait_schema = trait_type_schema[trait_qualifier]

                    # get the trait for the key
                    versions = dict()
                    if trait_qualifier is None:
                        # This is a map at this level
                        column_defs = ''
                        column_type = ''
                        create_query = 'Create table hive.sami_test.' + trait_type + ' ('
                        for branch in trait_schema:
                            versions = trait_schema[branch]
                            for version in versions:
                                branch_version = branch + '-' + version
                                col_type = 'struct<'
                                trait_properties = versions[version]['trait_properties']
                                for property in trait_properties:
                                    # name = property['name']
                                    # type = property['type']
                                    col_type += trait_properties[property]['name'] + ' ' + \
                                                trait_properties[property]['type'] + ','

                                #If there are subtraits, we need to handle them as well
                                #if not len(versions[version]['sub_traits']) is 0:
                                col_type = handleSubTraits(versions[version]['sub_traits'], col_type)
                                col_type = col_type[:-1] + '>'
                                create_query += branch_version + ' ' + col_type + ','
                                #create_query += column_defs + ','
                        create_query = create_query[:-1] + ')'

                        # for trait_key in archive.available_traits.get_all_traitkeys(trait_name_filter=trait_type):
                        #     try:
                        #         trait = sample[object_id][trait_key]
                        #     except DataNotAvailable:
                        #         continue
                        #
                        #     #
                        #     if trait.branch is None:
                        #         branch_version = 'No_branch'
                        #     else:
                        #         branch_version = trait.branch + '-' + trait.version
                        #
                        #     # get the schema for this key
                        #
                        #     col_type = 'struct< '              #Is this impala specific?
                        #     for property in trait_schema:
                        #         type = trait_schema[property]
                        #         if 'array' in type:
                        #             #TODO we have to get the dimension of the array from trait
                        #             pass
                        #         col_type += property + ' ' + type + ','
                        #     col_type = col_type[:-1] + '>'
                        #     create_query += branch_version + ' ' + col_type
                    else:
                        #table_name += '-' + trait_qualifier
                        #create_query += '-' + trait_qualifier + ' '
                        create_query = 'Create table hive.sami_test.' + trait_type + '-' + trait_qualifier + ' ('
                        # Now do the columns
                        column_defs = ''
                        for branch in trait_schema:
                            versions = trait_schema[branch]
                            for version in versions:
                                branch_version = branch + '-' + version
                                col_type = 'struct<'
                                trait_properties = versions[version]['trait_properties']
                                for property in trait_properties:
                                    name = trait_properties[property]['name']
                                    type = trait_properties[property]['type']
                                    col_type += trait_properties[property]['name'] + ' ' + \
                                                trait_properties[property]['type'] + ','
                                #if not len(versions[version]['sub_traits']) is 0:
                                col_type = handleSubTraits(versions[version]['sub_traits'], col_type)
                                col_type = col_type[:-1] + '>'
                                create_query += branch_version + ' ' + col_type + ','
                            #create_query += column_defs + ','
                        create_query = create_query[:-1] + ')'

                    # Execute create table query
                    print(create_query)



            break # We only need the first object


    except:
        pass


    print("Writing complete.")





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest astronomical objects')
    parser.add_argument('-t', '--table', required=True, help='the impala table of the already ingested data')
    parser.add_argument('input_dir', help='input data directory')
    parser.add_argument('catalogue', help='data catalogue')
    parser.add_argument('output_file', help='the path of the avro file to write data to')
    args = parser.parse_args()

    main(args)