import traceback
from numpy import ndarray
from numpy import int64

from fidia.exceptions import *
from fidia.ingest.properties import *

def get_traitproperty_data(trait):
    # type: (Trait) -> dict
    """Retrieve data for all trait properties attached to the Trait."""
    # Get data for TraitProperties, and store it in the following dicts.
    # trait_property_type = dict()
    trait_property_data = dict()
    for trait_property_name in trait.trait_property_dir():
        # trait_property_type[trait_property_name] = getattr(trait, trait_property_name).type
        t_p_name = trait_property_name
        # If trait_property_name is an impala reserved_word add 'res_' prefix to it
        if trait_property_name in IMPALA_RESERVED_WORDS:
            trait_property_name = 'res_' + trait_property_name
        try:
            trait_property_data[trait_property_name] = getattr(trait, t_p_name).value
            if isinstance(trait_property_data[trait_property_name], ndarray):
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

        sub_trait = trait.sub_traits.retrieve_with_key(sub_trait_name)
        sub_trait_data[sub_trait_name] = get_trait_data(sub_trait)
    return sub_trait_data

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
    #result.update({"sub_trait_data": sub_trait_data})
    result.update(sub_trait_data)

    return result
