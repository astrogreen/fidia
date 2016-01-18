from __future__ import absolute_import, division, print_function, unicode_literals

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)

log.enable_console_logging()

import re
from glob import glob
import os.path

import re

from astropy.io import fits
import pandas as pd


# FIDIA Relative Imports
from fidia import *
from .archive import Archive
from ..galaxy import Galaxy

from ..traits.utilities import TraitKey, TraitMapping, trait_property
from ..traits.base_traits import SpectralCube

sami_cube_re = re.compile(
        r"""(?P<sami_id>\d+)_
            (?P<color>red|blue)_
            (?P<n_comb>\d)_
            (?P<plate_id>Y\d\dSAR\d_P\d+_\d+T\d+)
            (?:_(?P<binning>1sec))?""", re.VERBOSE)

def find_all_cubes_for_id(base_directory, sami_id):
    log.debug("Finding cubes for id '%s'", sami_id)
    sami_id = str(sami_id)
    cubes = glob(base_directory + "*/cubed/" + sami_id + "/*")
    log.debug("Raw cube files found: %s", cubes)
    trim_length = len(base_directory)
    cubes = map(lambda s: s[trim_length:], cubes)
    result = dict()
    for file in cubes:
        run_id = file.split("/")[0]
        filename = file.split("/")[-1]
        cube_matches = sami_cube_re.match(filename)
        assert cube_matches.group('sami_id') == sami_id
        color = cube_matches.group('color')
        n_comb = cube_matches.group('n_comb')
        plate_id = cube_matches.group('plate_id')
        binning = cube_matches.group('binning')
        result[(sami_id, color, plate_id, binning)] = (run_id, filename)
        log.debug("id: %s, color: %s, plate: %s, bin: %s\n    -> run: %s, file: %s",
                  sami_id, color, plate_id, binning, run_id, filename)
    log.debug("Cube finding complete")
    return result


class SAMISpectralCube(SpectralCube):
    """Load a SAMI Data cube.

    TraitName is "color.plate_id.binning":

        color: (red|blue)
        plate_id: ex. Y15SAR3_P002_12T085
        binning: (|1sec)

    """
    # @classmethod
    # def data_available(cls, object_id):
    #     """Return a list of unique identifiers which can be used to retrieve actual data."""
    #     # Need to know the directory of the archive
    #     cube_files = glob(archive._base_directory_path + "*/cubed/" + object_id + "/*")
    #     return cube_files

    def __init__(self, archive, key):
        self.object_id = key.object_id
        self.archive = archive
        self._trait_name = key.trait_name
        self._color = key.trait_name.split(".")[0]
        self._plate_id = key.trait_name.split(".")[1]
        self._binning = key.trait_name.split(".")[2]

        available_cubes = find_all_cubes_for_id(self.archive._base_directory_path, self.object_id)
        log.debug("Finding cube for id: %s, color: %s, plate: %s, binning: %s",
                  self.object_id, self._color, self._plate_id, self._binning)
        try:
            self.run_id, self.cube_file = available_cubes[(self.object_id, self._color, self._plate_id, self._binning)]
        except KeyError:
            raise DataNotAvailable()

        self._cube_path = (self.archive._base_directory_path + "/"+ self.run_id + "/cubed/"
                           + self.object_id + "/" + self.cube_file)

        self.hdu = fits.open(self._cube_path)
        super(SAMISpectralCube, self).__init__(key)

    def cleanup(self):
        self.hdu.close()

    @property
    def shape(self):
        return 0

    @trait_property
    def value(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        key = str('PRIMARY')
        return self.hdu[key].data

    @trait_property
    def variance(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self.hdu[str('VARIANCE')].data

    @trait_property
    def covariance(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self.hdu[str('COVAR')].data

    @trait_property
    def weight(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self.hdu[str('WEIGHT')].data


class SAMITeamArchive(Archive):

    def __init__(self, base_directory_path, master_catalog_path):
        self._base_directory_path = base_directory_path
        self._master_catalog_path = master_catalog_path
        self._contents = None

        # Local cache for traits
        self._trait_cache = dict()

        super(SAMITeamArchive, self).__init__()


    @property
    def contents(self):
        """List (set?) of available objects in this archive."""
        if self._contents is None:
            with fits.open(self._master_catalog_path) as m:
                # Master Catalogue is a binary table in extension 1 of the FITS File.
                self._contents = list(map(str, m[1].data['CATID']))
        return self._contents

    def data_available(self, object_id=None):
        if object_id is None:
            raise NotImplementedError("Don't know what data is available for the whole survey.")
        else:
            #self.validate_id(object_id)
            if object_id in self._cubes_available():
                print("Cubes available.")

    def can_provide(self, trait_key):
        # TODO: Implement!
        return True

    def _cubes_available(self):
        """Generate a list of objects which have "cubed" directories."""
        cube_ids = map(os.path.basename,glob(self._base_directory_path + "*/cubed/*"))

        # Note, there may be duplicates; the following prints a list of duplicates
        #print [item for item, count in collections.Counter(cube_ids).items() if count > 1]
        return cube_ids

    @property
    def name(self):
        return 'SAMI'

    def define_available_traits(archive):

        archive.available_traits[TraitKey('spectral_cubes', None, None)] = SAMISpectralCube

        return archive.available_traits
