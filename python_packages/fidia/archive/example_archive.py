from __future__ import absolute_import, division, print_function, unicode_literals

# Python Standard Library Imports

import fidia
# from fidia.traits.references import ColumnReference
from fidia.traits import *

#
# class SimpleTrait(Trait):
#     """Description for SimpleTrait.
#
#     Extended documentation for SimpleTrait.
#
#     Some *markdown* formatted **text** and math: $\int_{\pi} f(x) dx$
#
#     ##format: markdown
#     """
#     # NOTE: Tests rely on this class, so changing it will require updating the tests!
#
#     trait_type = "simple_trait"
#
#     branches_versions = {'default': ['ver0']}
#     defaults = DefaultsRegistry('default', {'default': 'ver0'})
#
#
#     @trait_property('float')
#     def value(self):
#         return 5.5
#     value.set_description("TheValue")
#     value.set_pretty_name("Value")
#
#     @trait_property('float.array.1')
#     def non_catalog_data(self):
#         return [1.1, 2.2, 3.3]
#     non_catalog_data.set_description("Some Non-catalog data")
#     non_catalog_data.set_pretty_name("Non-catalog Data")
#
#     @trait_property('string')
#     def extra(self):
#         return "Extra info"
#     extra.set_description("ExtraInformation")
#     extra.set_pretty_name("Extra Info")
#
# class SimpleTraitWithSubtraits(Trait):
#
#     # NOTE: Tests rely on this class, so changing it will require updating the tests!
#
#     trait_type = "simple_heir_trait"
#
#     branches_versions = {'default': ['ver0']}
#     defaults = DefaultsRegistry('default', {'default': 'ver0'})
#
#     sub_traits = TraitRegistry()
#
#     @sub_traits.register
#     class SubTrait(SimpleTrait):
#         trait_type = 'sub_trait'
#
#     @trait_property('float')
#     def value(self):
#         return 5.5
#
#     @trait_property('float.array.1')
#     def non_catalog_data(self):
#         return [1.1, 2.2, 3.3]
#
#     @trait_property('string')
#     def extra(self):
#         return "Extra info"


class ExampleArchive(fidia.BasePathArchive):

    archive_id = "ExampleArchive"

    def __init__(self, **kwargs):
        # NOTE: Tests rely on `_contents`, so changing it will require updating the tests
        self._contents = ['Gal1', 'Gal2', 'Gal3']

        # Local cache for traits
        self._trait_cache = dict()

        super(ExampleArchive, self).__init__(**kwargs)

    # basedir = "hi"

    column_definitions = fidia.ColumnDefinitionList([
        ("red_image", fidia.FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0,
                                           ndim=2,
                                           timestamp=1)),
        ("red_image_exposed", fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "EXPOSED",
                                                     timestamp=1)),
        ("red_cube", fidia.FITSDataColumn("{object_id}/{object_id}_spec_cube.fits", 0,
                                          timestamp=1)),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRVAL1", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRVAL2", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRPIX1", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRPIX2", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CDELT1", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CDELT2", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CTYPE1", timestamp=1),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CTYPE2", timestamp=1),
        fidia.FITSBinaryTableColumn("stellar_masses.fits", 1, 'StellarMass', 'ID', timestamp=1),
        fidia.FITSBinaryTableColumn("stellar_masses.fits", 1, 'StellarMassError', 'ID', timestamp=1),
        fidia.FITSBinaryTableColumn("sfr_table.fits", 1, 'SFR', 'ID', timestamp=1),
        fidia.FITSBinaryTableColumn("sfr_table.fits", 1, 'SFR_ERR', 'ID', timestamp=1)
    ])


    trait_mappings = [
        TraitMapping(Image, 'red', [
            TraitPropertyMapping('data', "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"),
            TraitPropertyMapping('exposed', "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1"),
            SubTraitMapping('wcs', ImageWCS, [
                TraitPropertyMapping('crpix1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL1]:1'),
                TraitPropertyMapping('crpix2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL2]:1'),
                TraitPropertyMapping('crval1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRPIX1]:1'),
                TraitPropertyMapping('crval2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRPIX2]:1'),
                TraitPropertyMapping('cdelt1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CDELT1]:1'),
                TraitPropertyMapping('cdelt2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CDELT2]:1'),
                TraitPropertyMapping('ctype1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE1]:1'),
                TraitPropertyMapping('ctype2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE2]:1')
            ])
        ]),
        # TraitMapping(SpectralCube, 'red', {
        #     'data': "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_spec_cube.fits[0]:1"}),
        TraitMapping(DMU, 'StellarMasses', [
            TraitMapping(Table, 'StellarMasses', [
                TraitPropertyMapping('stellar_mass', 'ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[StellarMass]:1'),
                TraitPropertyMapping('stellar_mass_error','ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[StellarMassError]:1')
            ]),
            TraitMapping(Table, 'StarFormationRates', [
                TraitPropertyMapping('sfr', 'ExampleArchive:FITSBinaryTableColumn:sfr_table.fits[1].data[SFR]:1'),
                TraitPropertyMapping('sfr_err', 'ExampleArchive:FITSBinaryTableColumn:sfr_table.fits[1].data[SFR_ERR]:1')
            ])
        ])
    ]

    """
    - !Image red:
        data: !property red_image
        exposed: !property red_image_exposed
        wcs: !trait ImageWCS
            crval1: !property FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header["CRVAL1"]
    - !SpectralMap red:
        data: !property "red_cube"
    - !DMU StellarMasses:
        
    """

    @property
    def contents(self):
        return self._contents

    @property
    def name(self):
        return 'ExampleArchive'

    # feature_catalog_data = [
    #     TraitPath('redshift', trait_property='value'),
    #     TraitPath('simple_trait', trait_property='value'),
    #     TraitPath('simple_trait', trait_property='extra')
    # ]


