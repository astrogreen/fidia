from __future__ import absolute_import, division, print_function, unicode_literals

# Python Standard Library Imports

import fidia
# from fidia.traits.references import ColumnReference
from fidia.traits import *

class ExampleArchive(fidia.ArchiveDefinition):

    archive_id = "ExampleArchive"
    name = "ExampleArchive"

    archive_type = fidia.BasePathArchive

    def __init__(self, **kwargs):
        # NOTE: Tests rely on `_contents`, so changing it will require updating the tests
        self._contents = ['Gal1', 'Gal2', 'Gal3']

        # Local cache for traits
        self._trait_cache = dict()

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
                TraitPropertyMapping('stellar_mass_error', 'ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[StellarMassError]:1')
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

