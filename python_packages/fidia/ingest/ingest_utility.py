import traceback
from numpy import ndarray
from numpy import int64

from fidia.exceptions import *
from fidia.ingest.properties import *

from avro.schema import *
from hdfs import InsecureClient
from hdfs.ext.avro import AvroWriter

def get_traitproperty_data(trait, subtrait):
    # type: (Trait) -> dict
    """Retrieve data for all trait properties attached to the Trait."""
    # Get data for TraitProperties, and store it in the following dicts.
    trait_property_type = dict()
    trait_property_data = dict()
    for trait_property_name in trait.trait_property_dir(include_hidden=True):
        if trait_property_name.startswith("covarloc_"):
            continue
        # trait_property_type[trait_property_name] = getattr(trait, trait_property_name).type
        t_p_name = trait_property_name
        # If trait_property_name is an impala reserved_word add 'res_' prefix to it
        if trait_property_name in IMPALA_RESERVED_WORDS:
            trait_property_name = 'res_' + trait_property_name
        try:
            trait_property_data[trait_property_name] = getattr(trait, t_p_name).value
            trait_property_type[trait_property_name] = getattr(trait, t_p_name).type
            if isinstance(trait_property_data[trait_property_name], ndarray):
                # if array dimensions are > 2, write to hdfs from here and just pass the path
                shape = trait_property_data[trait_property_name].shape
                data_type = trait_property_type[trait_property_name].split('.')[0]
                if len(shape) > 2:
                    if len(shape) is 3:
                        items = ArraySchema(ArraySchema(ArraySchema(PrimitiveSchema(data_type))))
                    elif len(shape) is 4:
                        items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(PrimitiveSchema(data_type)))))
                    elif len(shape) is 5:
                        items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(ArraySchema(
                                PrimitiveSchema(data_type))))))
                    elif len(shape) is 6:
                        items = ArraySchema(ArraySchema(ArraySchema(ArraySchema(ArraySchema(
                                ArraySchema(PrimitiveSchema(data_type)))))))
                    else:
                        print("Array size is not supported. Size : ")
                        continue

                    meta_fields = list()
                    meta_fields.append(Field(PrimitiveSchema(STRING), "object_id", 1, False))
                    meta_fields.append(Field(PrimitiveSchema(STRING), "trait_type", 2, False))
                    meta_fields.append(Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(STRING)]),
                                             "trait_qualifier", 3, False))
                    meta_fields.append(Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(STRING)]),
                                             "branch", 4, False))
                    meta_fields.append(Field(UnionSchema([PrimitiveSchema(NULL), PrimitiveSchema(STRING)]),
                                             "version", 5, False))
                    meta_fields.append(Field(PrimitiveSchema(STRING), "trait_property", 6, False))
                    metadata_field = Field(RecordSchema("metadata", "trait_property", meta_fields, names=Names()),
                                           "metadata", 1, False)

                    data_field = Field(items, "data", 2, False)
                    record_schema = RecordSchema("cubic_property", "asvo.model.astro_object",
                                                 [metadata_field, data_field], names=Names())
                    record_json = record_schema.to_json()

                    if subtrait:
                        trait_type = trait.trait_path[0].trait_type
                        trait_qualifier = trait.trait_path[0].trait_qualifier
                    else:
                        trait_type = trait.trait_type
                        trait_qualifier = trait.trait_qualifier

                    if trait_qualifier is None:
                        trait_qualifier = ''
                    else:
                        trait_qualifier = '/' + trait_qualifier
                    if trait.branch is None:
                        branch_version = '/'
                    else:
                        branch_version = '/' + trait.branch + '/' + trait.version + '/'

                    base_path = 'Sami_Test/Sami_Data_Cubes/' + trait.object_id + '/' + trait_type + trait_qualifier + \
                                branch_version

                    meta_record = dict()
                    meta_record['object_id'] = trait.object_id
                    meta_record['trait_type'] = trait_type
                    meta_record['trait_qualifier'] = trait_qualifier
                    meta_record['branch'] = trait.branch
                    meta_record['version'] = trait.version
                    if subtrait:
                        meta_record['trait_property'] = trait.trait_type + '.' + trait_property_name
                        file_name = base_path + trait.trait_type + '/' + trait_property_name + '.avro'
                    else:
                        meta_record['trait_property'] = trait_property_name
                        file_name = base_path + trait_property_name + '.avro'

                    data_record = dict()
                    data_record['metadata'] = meta_record
                    data_record['data'] = trait_property_data[trait_property_name].tolist()

                    with AvroWriter(get_hdfs_client(), file_name, record_json, overwrite=True) as writer:
                        writer.write(data_record)
                    trait_property_data[trait_property_name] = file_name
                else:
                    trait_property_data[trait_property_name] = trait_property_data[trait_property_name].tolist()

            #TODO convert numpy.int64 to native python type
            if isinstance(trait_property_data[trait_property_name], int64):
                print("wrong data type. int64")
                trait_property_data[trait_property_name] = trait_property_data[trait_property_name].item()
        except DataNotAvailable:
            # No data for this particular TraitProperty, skip.
            # trait_property_type[trait_property_name] = None
            trait_property_data[trait_property_name] = None
            continue
        except:
            # Unable to retrieve the trait property for some reason. Skip for now.
            # TODO: Provide a warning
            tb = traceback.format_exc()
            print(tb)
            # trait_property_type[trait_property_name] = None
            trait_property_data[trait_property_name] = None
            continue

    # return {"trait_property_types": trait_property_type,
    #         "trait_property_data": trait_property_data}
    return trait_property_data


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

        #sub_trait = trait.sub_traits.retrieve_with_key(sub_trait_name)
        sub_trait_data[sub_trait_name] = get_trait_data(trait[sub_trait_name], True)
    return sub_trait_data

def get_trait_data(trait, subtrait=False):
    # type: (Trait) -> dict
    """Retrieve data for TraitProperties and sub-Traits attached to the Trait"""

    result = dict()

    # Get data for TraitProperties
    trait_property_data = get_traitproperty_data(trait, subtrait)
    # Add TraitProperty data to result
    result.update(trait_property_data)

    # Get data for sub-Traits
    sub_trait_data = get_sub_trait_data(trait)
    # Add sub_trait_data to result
    #result.update({"sub_trait_data": sub_trait_data})
    result.update(sub_trait_data)

    return result

def get_hdfs_client():
    client = InsecureClient("http://asvotest1.aao.gov.au:50070", 'lharischandra')
    return client