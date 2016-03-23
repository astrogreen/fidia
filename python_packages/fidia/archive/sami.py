from __future__ import absolute_import, division, print_function, unicode_literals

from glob import glob
import os.path
import datetime
import re
import time

from astropy import wcs
from astropy.io import fits

import pandas as pd

from cached_property import cached_property

# FIDIA Relative Imports
from fidia import *
from .archive import Archive

from ..utilities import WildcardDictionary

from fidia.traits import TraitKey, trait_property, SpectralMap, Image, VelocityMap

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()


# SAMI Cube file and plate ID regular expressions
#
# Cube files have names like:
#     41144_blue_7_Y14SAR3_P004_12T055_1sec.fits.gz
#     41144_blue_7_Y14SAR3_P004_12T055.fits.gz
#     41144_red_7_Y14SAR3_P004_12T055_1sec.fits.gz
#     41144_red_7_Y14SAR3_P004_12T055.fits.gz
#     41144_blue_7_Y15SAR3_P002_12T085_1sec.fits.gz
#     41144_blue_7_Y15SAR3_P002_12T085.fits.gz
#     41144_red_7_Y15SAR3_P002_12T085_1sec.fits.gz
#     41144_red_7_Y15SAR3_P002_12T085.fits.gz
#
# SAMI plate ID Definition:
#
#     Y<year>S<semester>R<obsrun>_P<platenumber>_<field1Region><field1Tile>_<field2Region><field2Tile>
#
#     e.g. Y16SAR2_P001_09T115_09T116
#
#     where
#     year=2016
#     semester=A
#     SAMI run within the semester = 2
#     plate for this run = 001
#     field 1 region = G09
#     field 1 tile = 115
#     field 2 region = G09
#     field 2 tile = 116
#
# Nuria says we decided on this nomenclature sometime between Oct-Dec 2012.
sami_plate_re = re.compile(
    r"""Y(?P<year>\d\d)
        S(?P<semester>(?:A|B))
        R(?P<run>\d+)_
        P(?P<plate_num>\d+)_
        (?P<ra>[A-Z0-9]+)
        T(?P<tile>\d+)
    """, re.VERBOSE
)

sami_cube_re = re.compile(
    r"""(?P<sami_id>\d+)_
        (?P<color>red|blue)_
        (?P<n_comb>\d+)_
        (?P<plate_id>%s)
        (?:_(?P<binning>1sec))?""" % sami_plate_re.pattern, re.VERBOSE)

def full_path_split(path):
    # Snippit from:
    # http://stackoverflow.com/questions/3167154/how-to-split-a-dos-path-into-its-components-in-python
    folders = []
    while 1:
        path, folder = os.path.split(path)
        if folder != "":
            folders.append(folder)
        else:
            break

    folders.reverse()
    return folders

def find_all_cubes_for_id(base_directory, sami_id):
    log.debug("Finding cubes for id '%s'", sami_id)
    sami_id = str(sami_id)
    cubes = glob(base_directory + "*/cubed/" + sami_id + "/*")
    log.debug("Raw cube files found: %s", cubes)
    trim_length = len(base_directory)
    cubes = map(lambda s: s[trim_length:], cubes)
    result = WildcardDictionary()
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

def cube_info_from_path(path):
    info = dict()
    info['filename'] = os.path.basename(path)
    log.debug("Filename: %s", info['filename'])
    matches = sami_cube_re.match(info['filename'])
    if matches is None:
        raise ValueError("Path '%s' does not appear to be a SAMI cube." % path)
    info['sami_id'] = matches.group('sami_id')
    info['color'] = matches.group('color')
    info['n_comb'] = matches.group('n_comb')
    info['plate_id'] = matches.group('plate_id')
    binning = matches.group('binning')
    log.debug("Binning is %s", binning)
    if binning is None:
        info['binning'] = "05"
    elif binning == "1sec":
        info['binning'] = "10"
    else:
        Exception("Unknown binning scheme found")
    info['run_id'] = full_path_split(path)[-4]
    info['path'] = path
    return info


class SAMIRowStackedSpectra(SpectralMap):
    """Load SAMI RSS data.

        TraitName is "run_id:rss_file_name":

        run_id: e.g. 2015_04_14-2015_04_22
        rss_file_name: e.g. 15apr20015sci.fits

    """

    trait_type = 'rss_map'


    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        return [TraitKey(cls.trait_type, "")]

    @classmethod
    def known_keys(cls, archive, object_id=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        # Need to know the directory of the archive
        known_keys = set()
        # Get RSS filenames from headers of cubes. Only need to sample one binning scheme, so we use "1sec"
        if object_id is None:
            # Search for all available data regardless of ID:
            cube_files = glob(archive._base_directory_path + "*/cubed/*/*_1sec.fits*")
        else:
            # Only return data for particular object_id provided
            cube_files = glob(archive._base_directory_path + "*/cubed/" + object_id + "/*_1sec.fits*")
        for f in cube_files:
            # Trim the base directory off the path and split into directories:
            dir_parts = f[len(archive._base_directory_path):].split("/")
            # RunId is first element:
            run_id = dir_parts[0]
            # Object ID is second to last element:
            object_id = dir_parts[-2]
            if object_id not in archive.contents:
                continue
            # Open file to get list of RSS files from header
            with fits.open(f) as hdu:
                index = 1
                while True:
                    try:
                        rss_filename = hdu[0].header['RSS_FILE ' + str(index)]
                    except KeyError:
                        break
                    else:
                        index += 1
                        known_keys.add(TraitKey(cls.trait_type, run_id + ":" + rss_filename, object_id=object_id))
            # Break out of the loop early for debuging purposes:
            if len(known_keys) > 50:
                break
        return known_keys


    def init(self):

        # Break apart and store the parts of the trait_name
        self._run_id = self.trait_name.split(":")[0]
        self._rss_filename = self.trait_name.split(":")[1]


        # Logic to construct full RSS filename
        #
        # It is necessary to construct a path that looks like
        #   "2015_04_14-2015_04_22/reduced/150415/Y15SAR3_P002_12T085_15T108/Y15SAR3_P002_15T108/main/ccd_1"
        # This looks hard, but actually, a given filename should really only appear once in the directory tree
        # below a given run_id, so we use `glob` to make this easier.

        self._rss_fits_filepath = self.archive._base_directory_path

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

    TraitName is "color.binning":

        color: (red|blue)
        binning*: (05|10)

        * The binning is optional: if it is omitted, a default will be set.

    TraitVersion is "plate_id":

        plate_id: ex. Y15SAR3_P002_12T085

        The plate_id is optional, if ommitted, then a default will be chosen.
    """

    trait_type = 'spectral_cube'

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        # Currently only knows about "red" and "blue" (because a default plate ID is chosen).
        return [TraitKey(cls.trait_type, 'red'), TraitKey(cls.trait_type, 'blue')]

    # @classmethod
    # def known_keys(cls, archive, object_id=None):
    #     """Return a list of unique identifiers which can be used to retrieve actual data."""
    #
    #     # @TODO: This still uses old code to determine the available keys instead of the cube_directory.
    #
    #     if object_id is None:
    #         # Return a list for all possible data
    #         cube_files = []
    #         for id in archive.contents:
    #              cube_files.extend(glob(archive._base_directory_path + "*/cubed/" + id + "/*.fits*"))
    #     else:
    #         # Only asked for data for a particular object_id
    #         cube_files = glob(archive._base_directory_path + "*/cubed/" + object_id + "/*.fits*")
    #
    #     # cube_files = glob(archive._base_directory_path + "*/cubed/*/*.fits*")
    #     known_keys = set(cls._traitkey_from_cube_path(f) for f in cube_files)
    #     return known_keys

    @classmethod
    def _traitkey_from_cube_path(cls, path):
        info = cube_info_from_path(path)
        return TraitKey(cls.trait_type, info['color'] + "." + info['binning'], info['plate_id'], info['sami_id'])

    def init(self):

        # Get necessary parameters from the trait_name, filling in defaults if necessary
        self._color = self.trait_name
        self._binning = "05"

        # Get necessary parameters from the trait_version, filling in defaults if necessary
        if self.trait_key.version is None:
            # Default requested. For now, we simply choose the first item
            # appearing in the archive's cube_directory.
            self._plate_id = self.archive._cubes_directory.ix[self.object_id, self._color, self._binning]\
                .reset_index()['plate_id'].iloc[0]
        else:
            self._plate_id = self.version

        # Confirm the requested data actually exists:
        try:
            path = self.archive._cubes_directory.ix[self.object_id, self._color, self._binning, self._plate_id]['path']
        except KeyError:
            log.error("Cannot retrieve cube info for key %s",
                      [self.object_id, self._color, self._binning, self._plate_id])
            raise DataNotAvailable("SAMISpectralCube data not available for {}".format(self.trait_key))
        else:
            if not isinstance(path, str):
                log.debug("Something's wrong, `path` is not a string?!, probably: ")
                log.debug("More than one cube file found for TraitKey %s", self.trait_key)
                raise MultipleResults("Multiple SAMISpectralCubes available for {}.".format(self.trait_key))

        self._cube_path = self.archive._cubes_directory\
            .ix[self.object_id, self._color, self._binning, self._plate_id]['path']

        # Add links to sub_traits
        # @TODO: Re-enable once RSS trait connection is understood (list of RSS files?)
        # self._sub_traits[TraitKey('rss', None, None, None)] = SAMIRowStackedSpectra


    def preload(self):
        self.hdu = fits.open(self._cube_path)


    def cleanup(self):
        self.hdu.close()

    @property
    def shape(self):
        return self.value.shape

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

    @trait_property('float')
    def total_exposure(self):
        """Total exposure time for this cube"""
        return self.hdu[0].header['TOTALEXP']

    @trait_property('string')
    def cubing_code_version(self):
        """Version of the cubing code used"""
        return self.hdu[0].header['HGCUBING']

    @trait_property('string')
    def plate_id(self):
        """Plate identification string"""
        return self.hdu[0].header['PLATEID']

    @trait_property('string')
    def plate_label(self):
        """Label assigned to the plate"""
        return self.hdu[0].header['LABEL']

    @trait_property('float')
    def ra(self):
        """Catalog right-ascension of the galaxy"""
        return self.hdu[0].header['CATARA']

    @trait_property('float')
    def dec(self):
        """Catalog declination of the galaxy."""
        return self.hdu[0].header['CATADEC']


    @trait_property('string.array')
    def source_rss_frames(self):
        source_rss_frames = []
        index = 1
        while True:
            try:
                rss_filename = self.hdu[0].header['RSS_FILE ' + str(index)]
            except KeyError:
                break
            else:
                source_rss_frames.append(rss_filename)
                index += 1
        return source_rss_frames

    @trait_property('string')
    def wcs_string(self):
        h = self.hdu[0].header.copy()
        # The PLATEID header keyword confuses the WCS package,
        # so it must be removed from the header before creating
        # the WCS object
        del h['PLATEID']
        w = wcs.WCS(h)
        return w.to_header_string()

    @cached_property
    def wcs(self):
        return wcs.WCS(self.wcs_string)


class LZIFUVelocityMap(VelocityMap):

    trait_type = "velocity_map"

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        known_keys = [TraitKey(cls.trait_type, None, None, None)]
        return known_keys

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev0.9/1_comp/" +
                           self.object_id + "_1_comp.fits.gz")
        try:
            self._hdu = fits.open(lzifu_fits_file)
        except:
            raise DataNotAvailable("No LZIFU data for SAMI ID '%s'" % self.object_id)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value.shape

    @property
    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        return self._hdu['V'].data[1, :, :]

    @trait_property('float.array')
    def variance(self):
        return self._hdu['V_ERR'].data[1, :, :]


class LZIFULineMap(Image):

    trait_type = 'line_map'

    line_name_map = {
        'OII3726': 'OII3726',
        'OII3729': 'OII3729',
        'HBETA': 'HBETA',
        # Note missing OIII4959, which is fit as 1/3rd of OIII50007
        'OIII5007': 'OIII5007',
        'OI6300': 'OI6300',
        # Note missing NII6548, which is fit as 1/3rd of NII6583
        'HALPHA': 'HALPHA',
        'NII6583': 'NII6583',
        'SII6716': 'SII6716',
        'SII6731': 'SII6731'
    }

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        known_keys = []
        for line in cls.line_name_map:
            known_keys.append(TraitKey(cls.trait_type, line, None, object_id))
        return known_keys

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev0.9/1_comp/" +
                           self.object_id + "_1_comp.fits.gz")
        self._hdu = fits.open(lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value.shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        value = self._hdu[self.line_name_map[self._trait_name]].data[1, :, :]
        log.debug("Returning type: %s", type(value))
        return value

    @trait_property('float.array')
    def variance(self):
        variance = self._hdu[self.line_name_map[self._trait_name] + '_ERR'].data[1, :, :]
        log.debug("Returning type: %s", type(variance))
        return variance


class LZIFUContinuum(SpectralMap):

    trait_type = 'spectral_continuum_cube'

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        known_keys = []
        for color in ('red', 'blue'):
            known_keys.append(TraitKey(cls.trait_type, color, None, object_id))
        return known_keys

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev0.9/1_comp/" +
                           self.object_id + "_1_comp.fits.gz")
        self._hdu = fits.open(lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value.shape

    @trait_property('float.array')
    def value(self):
        # Determine which colour:
        if self._trait_name == "blue":
            color = "B"
        elif self._trait_name == "red":
            color = "R"
        else:
            raise ValueError("unknown trait name")
        return self._hdu[color + '_CONTINUUM'].data

    @trait_property('float.array')
    def variance(self):
        return None

class LZIFULineSpectrum(SpectralMap):

    trait_type = 'spectral_line_cube'

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        known_keys = []
        for color in ('red', 'blue'):
            known_keys.append(TraitKey(cls.trait_type, color, None, object_id))
        return known_keys

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev0.9/1_comp/" +
                           self.object_id + "_1_comp.fits.gz")
        self._hdu = fits.open(lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value.shape

    @trait_property('float.array')
    def value(self):
        # Determine which colour:
        if self._trait_name == "blue":
            color = "B"
        elif self._trait_name == "red":
            color = "R"
        else:
            raise ValueError("unknown trait name")
        return self._hdu[color + '_LINE'].data

    @trait_property('float.array')
    def variance(self):
        return None

class SAMITeamArchive(Archive):

    def __init__(self, base_directory_path, master_catalog_path):
        self._base_directory_path = base_directory_path
        self._master_catalog_path = master_catalog_path
        self._contents = None

        self._cubes_directory = self._get_cube_info()

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

    def _get_cube_info(self):
        cube_file_paths = []
        for id in self.contents:
             cube_file_paths.extend(glob(self._base_directory_path + "*/cubed/" + id + "/*.fits*"))
        cube_directory = []
        for path in cube_file_paths:
            info = cube_info_from_path(path)
            cube_directory.append(info)
        cube_directory = pd.DataFrame(cube_directory)
        cube_directory.set_index(['sami_id', 'color', 'binning', 'plate_id'], inplace=True)
        return cube_directory

    def data_available(self, object_id=None):
        if object_id is None:
            raise NotImplementedError("Don't know what data is available for the whole survey.")
        else:
            #self.validate_id(object_id)
            if object_id in self._cubes_available():
                print("Cubes available.")

    def _cubes_available(self):
        """Generate a list of objects which have "cubed" directories."""
        cube_ids = map(os.path.basename, glob(self._base_directory_path + "*/cubed/*"))

        # Note, there may be duplicates; the following prints a list of duplicates
        #print [item for item, count in collections.Counter(cube_ids).items() if count > 1]
        return cube_ids

    @property
    def name(self):
        return 'SAMI'

    def define_available_traits(self):

        # Trait 'spectral_cube'
        self.available_traits[TraitKey(SAMISpectralCube.trait_type, None, None, None)] = SAMISpectralCube
        # Trait 'rss_map' (now a sub-trait of spectral_cube above.)
        # self.available_traits[TraitKey(SAMIRowStackedSpectra.trait_type, None, None, None)] = SAMIRowStackedSpectra

        # LZIFU Items

        self.available_traits[TraitKey('velocity_map', None, None, None)] = LZIFUVelocityMap
        self.available_traits[TraitKey('line_map', None, None, None)] = LZIFULineMap
        self.available_traits[TraitKey('spectral_line_cube', None, None, None)] = LZIFULineSpectrum
        self.available_traits[TraitKey('spectral_continuum_cube', None, None, None)] = LZIFUContinuum

        if log.isEnabledFor(slogging.DEBUG):
            log.debug("------Available traits--------")
            for key in self.available_traits:
                log.debug("   Key: %s", key)

        return self.available_traits
