from __future__ import absolute_import, division, print_function, unicode_literals

# Python Standard Library Imports
import os


import fidia
# from fidia.traits.references import ColumnReference
from fidia.traits import *

__all__ = ['ExampleArchive']

class ExampleArchive(fidia.ArchiveDefinition):
    """An Archive containing example data for use in testing and as an example.

    A data set for this archive can be generated using `fidia_tests/generate_test_data.py`

    """


    archive_id = "ExampleArchive"

    archive_type = fidia.BasePathArchive


    # For general testing, this should be set to True (commented out)
    # For testing of the system without database persistence, it should be False.
    # is_persisted = False

    def __init__(self, **kwargs):

        # Local cache for traits
        self._trait_cache = dict()

        basepath = kwargs["basepath"]

        # Populate contents based on what is actually present in the provided test dataset.
        with open(os.path.join(basepath, "object_list.txt")) as f:
            self.contents = [t.strip() for t in f.readlines()]

    column_definitions = fidia.ColumnDefinitionList([
        ("red_image", fidia.FITSDataColumn("{object_id}/{object_id}_red_image.fits", 0,
                                           ndim=2,
                                           timestamp=1, dtype="float64")),
        ("red_image_exposed", fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "EXPOSED",
                                                     timestamp=1, dtype="float64")),
        ("red_cube", fidia.FITSDataColumn("{object_id}/{object_id}_spec_cube.fits", 0,
                                          timestamp=1, dtype="float64")),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRVAL1", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRVAL2", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRPIX1", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CRPIX2", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CDELT1", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CDELT2", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CTYPE1", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "CTYPE2", timestamp=1, dtype="float64"),
        fidia.FITSHeaderColumn("{object_id}/{object_id}_red_image.fits", 0, "NAXIS", timestamp=1, dtype="int64"),
        fidia.FITSBinaryTableColumn("stellar_masses.fits", 1, 'StellarMass', 'ID', timestamp=1),
        fidia.FITSBinaryTableColumn("stellar_masses.fits", 1, 'StellarMassError', 'ID', timestamp=1),
        fidia.FITSBinaryTableColumn("sfr_table.fits", 1, 'SFR', 'ID', timestamp=1),
        fidia.FITSBinaryTableColumn("sfr_table.fits", 1, 'SFR_ERR', 'ID', timestamp=1),
        ("png_image", fidia.RawFileColumn("{object_id}/{object_id}_spectra.png", timestamp=1, dtype="bytes"))
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
        TraitMapping(SpectralCube, 'red', [
            TraitPropertyMapping('data', "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_spec_cube.fits[0]:1")
        ]),
        TraitMapping(DMU, 'StellarMasses', [
            TraitMapping(Table, 'StellarMasses', [
                TraitPropertyMapping('stellar_mass', 'ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[ID->StellarMass]:1'),
                TraitPropertyMapping('stellar_mass_error', 'ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[ID->StellarMassError]:1')
            ]),
            TraitMapping(Table, 'StarFormationRates', [
                TraitPropertyMapping('sfr', 'ExampleArchive:FITSBinaryTableColumn:sfr_table.fits[1].data[ID->SFR]:1'),
                TraitPropertyMapping('sfr_err', 'ExampleArchive:FITSBinaryTableColumn:sfr_table.fits[1].data[ID->SFR_ERR]:1')
            ])
        ]),
        TraitMapping(PixelImage, "spectra", [
            TraitPropertyMapping('bytes', "png_image")
        ]),
        TraitMapping(FITSFile, "red_image", [
            TraitMapping(FitsImageHdu, 'PRIMARY', [
                TraitPropertyMapping('data', "ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"),
                TraitMapping(FITSHeader, 'header', [
                    TraitPropertyMapping('naxis', "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[NAXIS]:1"),
                    TraitPropertyMapping('exposed', "ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[EXPOSED]:1"),
                    TraitPropertyMapping('crpix1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL1]:1'),
                    TraitPropertyMapping('crpix2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRVAL2]:1'),
                    TraitPropertyMapping('crval1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRPIX1]:1'),
                    TraitPropertyMapping('crval2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CRPIX2]:1'),
                    TraitPropertyMapping('cdelt1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CDELT1]:1'),
                    TraitPropertyMapping('cdelt2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CDELT2]:1'),
                    TraitPropertyMapping('ctype1', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE1]:1'),
                    TraitPropertyMapping('ctype2', 'ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[CTYPE2]:1')
                ])
            ])
        ])
    ]
    #
    # """
    # - !Image red:
    #     data: !property red_image
    #     exposed: !property red_image_exposed
    #     wcs: !trait ImageWCS
    #         crval1: !property FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header["CRVAL1"]
    # - !SpectralMap red:
    #     data: !property "red_cube"
    # - !DMU StellarMasses:
    #
    # """

