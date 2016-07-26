import traceback


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
            # array_dict = dict()
            if hasattr(trait_property_data[trait_property_name], 'shape'):
                # Shape attribute can provide the shape of the data (probably a
                # numpy array).
                # array_dict['shape'] = str(trait_property_data[trait_property_name].shape)
                # array_dict['dataValues'] = trait_property_data[trait_property_name].flatten().tolist()
                array_tuple = (trait_property_data[trait_property_name].flatten().tolist(),
                               str(trait_property_data[trait_property_name].shape))

            elif isinstance(trait_property_data[trait_property_name], list):
                # A one-dimensional Python list.
                # array_dict['shape'] = "({})".format(len(trait_property_data[trait_property_name]))
                # array_dict['dataValues'] = trait_property_data[trait_property_name]
                array_tuple = (trait_property_data[trait_property_name],
                               "({})".format(len(trait_property_data[trait_property_name])))
            else:
                # Unknown array format. Skip.
                continue

            # Replace the trait_property_data with the modified, array-format version:
            trait_property_data[trait_property_name] = array_tuple

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
