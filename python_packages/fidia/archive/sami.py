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

#from fidia.traits import TraitKey, trait_property, SpectralMap, Image, VelocityMap
from fidia.traits import *
from fidia.traits.utilities import TraitMapping

from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.INFO)
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
                        known_keys.add(TraitKey(cls.trait_type, run_id + ":" + rss_filename))
            # Break out of the loop early for debuging purposes:
            if len(known_keys) > 50:
                break
        return known_keys


    def init(self):

        # Break apart and store the parts of the trait_qualifier
        self._run_id = self.trait_qualifier.split(":")[0]
        self._rss_filename = self.trait_qualifier.split(":")[1]


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

        log.debug("TraitKey: %s", self.trait_key)
        # Get necessary parameters from the trait_qualifier, filling in defaults if necessary
        if self.trait_qualifier in ('blue', 'red'):
            self._color = self.trait_qualifier
        else:
            raise DataNotAvailable("SAMISpectralCube data not available for colour %s" % self.trait_qualifier)
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
        return self.value().shape

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


    #
    # Sub Traits
    #

    _sub_traits = TraitMapping()


    class CatCoordinate(SkyCoordinate):

        @trait_property('float')
        def _ra(self):
            return self.parent_trait.ra()

        @trait_property('float')
        def _dec(self):
            return self.parent_trait.dec()

    _sub_traits[TraitKey('catalog_coordinate')] = CatCoordinate

    class WCS(WorldCoordinateSystem):

        @trait_property('string')
        def _wcs_string(self):
            with self.parent_trait.preloaded_context() as pt:
                h = pt.hdu[0].header.copy()
                # The PLATEID header keyword confuses the WCS package,
                # so it must be removed from the header before creating
                # the WCS object
                del h['PLATEID']
                w = wcs.WCS(h)
                return w.to_header_string()

    _sub_traits[TraitKey('wcs')] = WCS


    class AAT(OpticalTelescopeCharacteristics):
        """AAT Telescope characteristics defined by FITS header

        Relevant section from the header:

            ORIGIN  = 'AAO     '           / Originating Institution
            TELESCOP= 'Anglo-Australian Telescope' / Telescope Name
            ALT_OBS =                 1164 / Altitude of observatory in metres
            LAT_OBS =            -31.27704 / Observatory latitude in degrees
            LONG_OBS=             149.0661 / Observatory longitude in degrees
        """

        trait_type = 'telescope_metadata'

        # trait_properties = [
        #     TraitPropertyFromFitsHeader(name='telescope', header_name='TELESCOP'),
        #     TraitPropertyFromFitsHeader(name='altitude', header_name='ALT_OBS'),
        #     TraitPropertyFromFitsHeader(name='latitude', header_name='LAT_OBS'),
        #     TraitPropertyFromFitsHeader(name='longitude', header_name='LONG_OBS'),
        # ]

        @trait_property('string')
        def telescope(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['TELESCOP']

        @trait_property('string')
        def altitude(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['ALT_OBS']

        @trait_property('string')
        def latitude(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['LAT_OBS']

        @trait_property('string')
        def longitude(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['LONG_OBS']

    _sub_traits[TraitKey('telescope_metadata')] = AAT

    class AAOmegaDetector(DetectorCharacteristics):
        """AAOmega Detector characteristics defined by FITS header

        Relevant section from the header:
            DCT_DATE= 'Sep 12 2014'        / DCT release date
            DCT_VER = 'r3_110_2_3'         / DCT version number
            DETECXE =                 2048 / Last column of detector
            DETECXS =                    1 / First column of detector
            DETECYE =                 4102 / Last row of detector
            DETECYS =                    1 / First row of detector
            DETECTOR= 'E2V2A   '           / Detector name
            XPIXSIZE=                  15. / X Pixel size in microns
            YPIXSIZE=                  15. / Y Pixel size in microns
            METHOD  = 'CCD Charge shuffling technique' / Observing method
            SPEED   = 'NORMAL  '           / Readout speed
            READAMP = 'RIGHT   '           / Readout amplifier
            RO_GAIN =                 1.88 / Readout amplifier (inverse) gain (e-/ADU)
            RO_NOISE=                 3.61 / Readout noise (electrons)

        """

        trait_type = 'detector_metadata'

        @trait_property('string')
        def detector_id(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['DETECTOR']
        detector_id.short_name = "DETECTOR"

        @trait_property('string')
        def gain(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['RO_GAIN']
        gain.short_name = "RO_GAIN"

        @trait_property('string')
        def read_noise(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['RO_NOISE']
        read_noise.short_name = 'RO_NOISE'

        @trait_property('string')
        def read_speed(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['SPEED']
        read_speed.short_name = 'SPEED'

        @trait_property('string')
        def detector_control_software_date(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['DCT_DATE']
        detector_control_software_date.short_name = 'DCT_DATE'

        @trait_property('string')
        def detector_control_software_version(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['DCT_VER']
        detector_control_software_version.short_name = 'DCT_VER'

        @trait_property('string')
        def read_amplifier(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['READAMP']
        read_amplifier.short_name = 'READAMP'

    _sub_traits[TraitKey('detector_metadata')] = AAOmegaDetector

    class SAMICharacteristics(SpectrographCharacteristics):
        """Characteristics of the SAMI Instrument

        Relevant Header Sections:

            RCT_VER = 'r3_71HB '           / Run Control Task version number
            RCT_DATE= '19-Oct-2013'        / Run Control Task version date
            RADECSYS= 'FK5     '           / FK5 reference system
            INSTRUME= 'AAOMEGA-SAMI'       / Instrument in use
            SPECTID = 'BL      '           / Spectrograph ID
            GRATID  = '580V    '           / Disperser ID
            GRATTILT=                  0.7 / Grating tilt to be symmetric (degree)
            GRATLPMM=                582.0 / Disperser ruling (lines/mm)
            ORDER   =                    1 / Spectrum order
            TDFCTVER= 'r11_33A '           / 2dF Control Task Version
            TDFCTDAT= '17-Oct-2014'        / 2dF Control Task Version Date
            DICHROIC= 'X5700   '           / Dichroic name
            OBSTYPE = 'OBJECT  '           / Observation type
            TOPEND  = 'PF      '           / Telescope top-end
            AXIS    = 'REF     '           / Current optical axis
            AXIS_X  =                   0. / Optical axis x (mm)
            AXIS_Y  =                   0. / Optical axis y (mm)
            TRACKING= 'TRACKING'           / Telescope is tracking.
            TDFDRVER= '1.34    '           / 2dfdr version
            PLATEID = 'Y14SAR3_P005_12T056_15T080' / Plate ID (from config file)
            LABEL   = 'Y14SAR3_P005_12T056 - Run 16 galaxy plate 5 - field 1' / Configuratio

        """

        trait_type = 'instrument_metadata'

        @trait_property('string')
        def instrument_id(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['INSTRUME']

        @trait_property('string')
        def spectrograph_arm(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['SPECTID']

        @trait_property('string')
        def disperser_id(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['GRATID']

        @trait_property('string')
        def disperser_tilt(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['GRATTILT']

        @trait_property('string')
        def instrument_software_version(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['TDFCTVER']

        @trait_property('string')
        def instrument_software_date(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['TDFCTDAT']

        @trait_property('string')
        def dichroic_id(self):
            with self.parent_trait.preloaded_context() as pt:
                return pt.hdu[0].header['DICHROIC']



    _sub_traits[TraitKey('instrument_metadata')] = SAMICharacteristics


class LZIFUVelocityMap(VelocityMap):

    trait_type = "velocity_map"

    default_version = "0.9b"
    available_versions = {"0.9b"}

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        known_keys = [TraitKey(cls.trait_type, None, None, None)]
        return known_keys

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev0.9b/recom_comp/" +
                           self.object_id + "_recom_comp.fits.gz")
        try:
            self._hdu = fits.open(lzifu_fits_file)
        except:
            raise DataNotAvailable("No LZIFU data for SAMI ID '%s'" % self.object_id)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value().shape

    @property
    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        return self._hdu['V'].data[1, :, :]

    @trait_property('float.array')
    def variance(self):
        return self._hdu['V_ERR'].data[1, :, :]


class LZIFUOneComponentLineMap(Image):

    trait_type = 'line_map'

    default_version = "0.9b"
    available_versions = {"0.9b", "0.9"}

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
            known_keys.append(TraitKey(cls.trait_type, line, None))
        return known_keys

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev" + self.version + "/1_comp/" +
                           self.object_id + "_1_comp.fits.gz")
        self._hdu = fits.open(lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value().shape

    def unit(self):
        return None

    @trait_property('float.array')
    def value(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[1, :, :]
        log.debug("Returning type: %s", type(value))
        return value

    @trait_property('float.array')
    def variance(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[1, :, :]
        log.debug("Returning type: %s", type(variance))
        variance = sigma**2
        return variance

class LZIFURecommendedMultiComponentLineMap(LZIFUOneComponentLineMap):

    available_versions = {"0.9b"}

    def preload(self):
        lzifu_fits_file = (self.archive._base_directory_path +
                           "/lzifu_releasev" + self.version + "/recom_comp/" +
                           self.object_id + "_recom_comp.fits.gz")
        self._hdu = fits.open(lzifu_fits_file)

    @trait_property('float.array')
    def value(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[0, :, :]
        log.debug("Returning type: %s", type(value))
        return value

    @trait_property('float.array')
    def variance(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[0, :, :]
        variance = sigma**2
        return variance

    # 1-component
    @trait_property('float.array')
    def comp_1_flux(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[1, :, :]
        return value

    @trait_property('float.array')
    def comp_1_variance(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[1, :, :]
        variance = sigma**2
        return variance

    @trait_property('float.array')
    def comp_2_flux(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[2, :, :]
        return value

    @trait_property('float.array')
    def comp_2_variance(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[2, :, :]
        variance = sigma**2
        return variance

    @trait_property('float.array')
    def comp_3_flux(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[3, :, :]
        return value

    @trait_property('float.array')
    def comp_3_variance(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[3, :, :]
        variance = sigma**2
        return variance

    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu[0].header
        return _wcs_string


    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self.parent_trait._wcs_string.value

    _sub_traits = TraitMapping()
    _sub_traits[TraitKey('wcs')] = LZIFUWCS

class LZIFUContinuum(SpectralMap):

    trait_type = 'spectral_continuum_cube'

    @classmethod
    def all_keys_for_id(cls, archive, object_id, parent_trait=None):
        """Return a list of unique identifiers which can be used to retrieve actual data."""
        known_keys = []
        for color in ('red', 'blue'):
            known_keys.append(TraitKey(cls.trait_type, color, None))
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
        return self.value().shape

    @trait_property('float.array')
    def value(self):
        # Determine which colour:
        if self.trait_qualifier == "blue":
            color = "B"
        elif self.trait_qualifier == "red":
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
            known_keys.append(TraitKey(cls.trait_type, color, None))
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
        return self.value().shape

    @trait_property('float.array')
    def value(self):
        # Determine which colour:
        if self.trait_qualifier == "blue":
            color = "B"
        elif self.trait_qualifier == "red":
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

        log.debug("master_catalog_path: %s", self._master_catalog_path)

        self._cubes_directory = self._get_cube_info()

        with fits.open(self._master_catalog_path) as m:
            fits_table = m[1].data
            self.tabular_data = pd.DataFrame.from_records(
                fits_table.tolist(),
                columns=map(lambda x: x.name, fits_table.columns))
        self.tabular_data.set_index('CATID')

        self._contents = set(self._cubes_directory.index.get_level_values('sami_id'))

        # Local cache for traits
        self._trait_cache = dict()

        super(SAMITeamArchive, self).__init__()

    @property
    def contents(self):
        """List (set?) of available objects in this archive."""
        return self._contents

    def _get_cube_info(self):
        cube_file_paths = []
        with fits.open(self._master_catalog_path) as m:
            # Master Catalogue is a binary table in extension 1 of the FITS File.
            contents = list(map(str, m[1].data['CATID']))
        for id in contents:
             cube_file_paths.extend(glob(self._base_directory_path + "*/cubed/" + id + "/*.fits*"))
        cube_directory = []
        for path in cube_file_paths:
            info = cube_info_from_path(path)
            cube_directory.append(info)
        cube_directory = pd.DataFrame(cube_directory)
        cube_directory.set_index(['sami_id', 'color', 'binning', 'plate_id'], inplace=True)
        return cube_directory

    def create_table_available_data(self, filename):
        # Create an empty data frame indexed by all of the SAMI sample
        table = pd.DataFrame(index=pd.Index(self.contents, name='sami_id'))
        # Generate a set of unique IDs for which there are cubes
        cube_list = set(self._cubes_directory.index.get_level_values('sami_id'))
        # Add this list to the data frame
        table['cube_available'] = pd.Series([True for i in range(len(cube_list))], index=pd.Index(cube_list))
        # The objects without cubes will have NaN; so fix that now by setting the not trues to explicitly False
        table.loc[table['cube_available'] != True, 'cube_available'] = False

        table['data_browser_url'] = pd.Series(['/asvo/data/sami/%s' % id for id in cube_list],
                                               index=pd.Index(cube_list))

        # Write to file
        with open(filename, 'w') as f:
            f.write(table.to_csv())

        # Then upload file to HDFS, and run a Hive query like the following:
        #
        #     DROP TABLE sami;
        #     CREATE EXTERNAL TABLE sami(
        #          sami_id STRING COMMENT 'SAMI ID (matches GAMA ID when the same object)',
        #          cube_available BOOLEAN COMMENT 'Is a cube available in the database',
        #          data_browser_url STRING COMMENT 'URL of the data browser'
        #       )
        #      COMMENT 'Table containing SAMI sample with observation information'
        #      ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'
        #      STORED AS TEXTFILE
        #      LOCATION '/user/agreen/sami_table.csv';

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

        self.available_traits[TraitKey('line_map', None, "1_comp", None)] = LZIFUOneComponentLineMap
        # self.available_traits[TraitKey('line_map', None, "recommended", None)] = LZIFURecommendedMultiComponentLineMap
        self.available_traits[TraitKey('line_map', None, None, None)] = LZIFURecommendedMultiComponentLineMap

        # self.available_traits[TraitKey('spectral_line_cube', None, None, None)] = LZIFULineSpectrum
        # self.available_traits[TraitKey('spectral_continuum_cube', None, None, None)] = LZIFUContinuum

        if log.isEnabledFor(slogging.DEBUG):
            log.debug("------Available traits--------")
            for key in self.available_traits:
                log.debug("   Key: %s", key)

        return self.available_traits
