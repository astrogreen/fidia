from fidia.archive.example_archive import ExampleArchive

ar = ExampleArchive()
sample = ar.get_full_sample()

# >> ar.schema()

# {'line_map': {'value': 'float.array', 'variance': 'float.array'},
#  'redshift': {'value': 'float'},
#  'simple_heir_trait': {'extra': 'string',
#   'sub_trait': {'extra': 'string', 'value': 'float'},
#   'value': 'float'},
#  'simple_trait': {'extra': 'string', 'value': 'float'},
#  'spectral_map': {'extra_value': 'float',
#   'galaxy_name': 'string',
#   'value': 'float.array',
#   'variance': 'float.array'},
#  'velocity_map': {'value': 'float.array', 'variance': 'float.array'}}

schema = ar.schema()
for trait in schema:
    for property_or_subtrait in schema[trait]:
        # print("Type of '{}.{}' is: {}".format(
        #     trait, property_or_subtrait, type(schema[trait][property_or_subtrait])))
        if isinstance(schema[trait][property_or_subtrait], dict):
            print("'{}.{}' is a sub_trait.".format(trait, property_or_subtrait))
        else:
            print("'{}.{}' is a property.".format(trait, property_or_subtrait))

