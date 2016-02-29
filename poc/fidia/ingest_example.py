import numpy as np

import fidia
from fidia.traits.base_traits import Trait
from fidia.archive.example_archive import ExampleArchive

ar = ExampleArchive()

schema = ar.schema()
sample = ar.get_full_sample()

def store_data_for_trait(hierarchy, trait):
    assert isinstance(trait, Trait)
    for trait_property_name in trait.trait_property_dir():
        data_to_store = getattr(trait, trait_property_name)

        # Need to put data_to_store at "location" hierarchy in the database

    # for sub_trait in trait.sub_trait_list():
    #     store_data_for_trait(hierarchy + (sub_trait.key,), sub_trait)

# Iterate over all objects in the sample:
for object_id in sample:
    # Iterate over all Traitkeys for this object:
    for trait_key in sample[object_id]:
        # Retrieve all TraitProperties for this Trait and recurse over sub-traits:
        store_data_for_trait((object_id, trait_key), sample[object_id][trait_key])
