from __future__ import absolute_import, division, print_function, unicode_literals

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
#log.enable_console_logging()

import re
from glob import glob
import os.path
import datetime
import re

from astropy.io import fits
import pandas as pd


# FIDIA Relative Imports
from fidia import *
from .archive import Archive
from ..galaxy import Galaxy

from ..traits.utilities import TraitKey, TraitMapping, trait_property
from ..traits.base_traits import SpectralMap

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
        if binning is None: binning = ""
        result[(sami_id, color, plate_id, binning)] = (run_id, filename)
        log.debug("id: %s, color: %s, plate: %s, bin: %s\n    -> run: %s, file: %s",
                  sami_id, color, plate_id, binning, run_id, filename)
    log.debug("Cube finding complete")
    return result

def obs_date_run_filename(run_id, filename):
    """Determine the date for a AAOmega filename and run_id"""

    # Work out the date of the observation

    # run ID is of the form START-END, e.g. "2015_04_14-2015_04_22"
    # Take the first part and create a date time object from it:
    start_date = run_id.split("-")[0]
    start_date = datetime.datetime.strptime(start_date, "%Y_%m_%d")

    # Convert date from filename (e.g. 15apr) into a date time object:
    rss_date = datetime.datetime.strptime(filename[0:5], "%d%b")

    # Determine year for file (by assuming that it is close to but after
    # the start date of the run: this is necessary to handle a run which
    # starts at the end of the year and finishes in the start of the next year)
    if rss_date.replace(year=start_date.year) < start_date:
        # The rss date is in the new year
        rss_date = rss_date.replace(year=start_date.year + 1)
    else:
        # The rss date is in the same year as the start date
        rss_date = rss_date.replace(year=start_date.year)

    return rss_date

class SAMIRowStackedSpectra(SpectralMap):
    """Load SAMI RSS data.

        TraitName is "run_id.rss_file_name":

        run_id: e.g. 2015_04_14-2015_04_22
        rss_file_name: e.g. 15apr20015sci.fits

    """

    def __init__(self, archive, trait_key):
        self.object_id = trait_key.object_id
        self.archive = archive
        self._trait_name = trait_key.trait_name

        # Break apart and store the parts of the trait_name
        self._run_id = trait_key.trait_name.split(":")[0]
        self._rss_filename = trait_key.trait_name.split(":")[1]


        # Logic to construct full RSS filename
        #
        # It is necessary to construct a path that looks like
        #   "2015_04_14-2015_04_22/reduced/150415/Y15SAR3_P002_12T085_15T108/Y15SAR3_P002_15T108/main/ccd_1"
        # This looks hard, but actually, a given filename should really only appear once in the directory tree
        # below a given run_id, so we use `glob` to make this easier.

        self._rss_fits_filepath = archive._base_directory_path

        # The Run ID section
        self._rss_fits_filepath += self._run_id
        self._rss_fits_filepath += "/"

        self._rss_fits_filepath += "reduced/"

        possible_paths = glob(self._rss_fits_filepath +
                              "*/*/*/main/ccd_?/" + self._rss_filename)

        if len(possible_paths) != 1:
            # Something's wrong if we don't have a single match!
            log.debug("RSS file not found, glob returned %s", possible_paths)
            raise DataNotAvailable()


        self._rss_fits_filepath = possible_paths[0]

        super(SAMIRowStackedSpectra, self).__init__(trait_key)

    def preload(self):
        self._hdu = fits.open(self._rss_fits_filepath)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        key = str('PRIMARY')
        return self._hdu[key].data

    @trait_property('float.array')
    def variance(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self._hdu[str('VARIANCE')].data

class SAMISpectralCube(SpectralMap):
    """Load a SAMI Data cube.

    TraitName is "color.plate_id.binning":

        color: (red|blue)
        plate_id: ex. Y15SAR3_P002_12T085
        binning: (|1sec)

    """
    # @classmethod
    # def data_available(cls, archive, trait_key):
    #     """Return a list of unique identifiers which can be used to retrieve actual data."""
    #     # Need to know the directory of the archive
    #     cube_files = glob(archive._base_directory_path + "*/cubed/" + object_id + "/*")
    #     return cube_files

    def __init__(self, archive, trait_key):
        self.object_id = trait_key.object_id
        self.archive = archive
        self._trait_name = trait_key.trait_name
        self._color = trait_key.trait_name.split(".")[0]
        self._binning = trait_key.trait_name.split(".")[1]
        self._plate_id = trait_key.version

        available_cubes = find_all_cubes_for_id(self.archive._base_directory_path, self.object_id)
        log.debug("Finding cube for id: %s, color: %s, plate: %s, binning: %s",
                  self.object_id, self._color, self._plate_id, self._binning)
        try:
            self.run_id, self.cube_file = available_cubes[(self.object_id, self._color, self._plate_id, self._binning)]
        except KeyError:
            raise DataNotAvailable(trait_key)

        self._cube_path = (self.archive._base_directory_path + "/"+ self.run_id + "/cubed/"
                           + self.object_id + "/" + self.cube_file)

        super(SAMISpectralCube, self).__init__(trait_key)

    def preload(self):
        self.hdu = fits.open(self._cube_path)


    def cleanup(self):
        self.hdu.close()

    @property
    def shape(self):
        return 0

    @trait_property('float.array')
    def value(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        key = str('PRIMARY')
        return self.hdu[key].data

    @trait_property('float.array')
    def variance(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self.hdu[str('VARIANCE')].data

    @trait_property('float.array')
    def covariance(self):
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self.hdu[str('COVAR')].data

    @trait_property('float.array')
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

    def _cubes_available(self):
        """Generate a list of objects which have "cubed" directories."""
        cube_ids = map(os.path.basename,glob(self._base_directory_path + "*/cubed/*"))

        # Note, there may be duplicates; the following prints a list of duplicates
        #print [item for item, count in collections.Counter(cube_ids).items() if count > 1]
        return cube_ids

    @property
    def name(self):
        return 'SAMI'

    def define_available_traits(self):

        self.available_traits[TraitKey('spectral_cube', None, None, None)] = SAMISpectralCube
        self.available_traits[TraitKey('rss_map', None, None, None)] = SAMIRowStackedSpectra

        if log.isEnabledFor(slogging.DEBUG):
            log.debug("------Available traits--------")
            for key in self.available_traits:
                log.debug("   Key: %s", key)

        return self.available_traits
