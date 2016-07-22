from __future__ import absolute_import, division, print_function, unicode_literals

from glob import glob
import os.path
import datetime
import re

from astropy import wcs
from astropy.io import fits
from astropy import units

import pandas as pd

from cached_property import cached_property

# FIDIA Relative Imports
from fidia import *
from .archive import Archive

from ..utilities import WildcardDictionary, DefaultsRegistry, exclusive_file_lock

#from fidia.traits import TraitKey, trait_property, SpectralMap, Image, VelocityMap
from fidia.traits import *
from fidia.traits.utilities import trait_property_from_fits_header

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

SAMI_RUN_NAME_RE = re.compile(
    r"""^(?P<start_date>\d{4}_\d{1,2}_\d{1,2})-
        (?P<end_date>\d{4}_\d{1,2}_\d{1,2})$""", re.VERBOSE)


class TraitFromFitsFile(Trait):

    def _post_init(self):
        self._fits_file_path = self.fits_file_path()
        if not os.path.exists(self._fits_file_path) and \
                os.path.exists(self._fits_file_path + ".gz"):
            self._fits_file_path = self._fits_file_path + ".gz"
        elif not os.path.exists(self._fits_file_path):
            raise DataNotAvailable(self._fits_file_path + " does not exist.")

        super()._post_init()

    def preload(self):
        self._hdu = fits.open(self._fits_file_path)

    def cleanup(self):
        self._hdu.close()

def trait_property_from_fits_data(extension_name, type, name):

    tp = TraitProperty(type=type, name=name)

    tp.fload = lambda self: self._hdu[extension_name].data
    tp.short_name = extension_name

    # # @TODO: Providence information can't get filename currently...
    # tp.providence = "!: FITS-Header {{file: '{filename}' extension: '{extension}' header: '{card_name}'}}".format(
    #     card_name=header_card_name, extension=extension, filename='UNDEFINED'
    # )

    return tp



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

    sub_traits = TraitRegistry()

    trait_type = 'rss_map'

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
    """Load a SAMI Data cube."""

    sub_traits = TraitRegistry()

    trait_type = 'spectral_map'
    qualifiers = {'red', 'blue'}

    def init(self):

        log.debug("TraitKey: %s", self.trait_key)
        self._color = self.trait_qualifier

        # Binning can be either '05' or '10'
        self._binning = "05"

        # We don't currently support multiple observations, so set the plate ID
        # to the first/only observation
        self._plate_id = self.archive._cubes_directory.ix[self.object_id, self._color, self._binning]\
            .reset_index()['plate_id'].iloc[0]

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
                raise Exception("Multiple SAMISpectralCubes available for {}.".format(self.trait_key))
            if not os.path.exists(path):
                raise DataNotAvailable("SAMISpectralCube data not available for {}".format(self.trait_key))

        self._cube_path = path

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

    # Add links to sub_traits
    # @TODO: Re-enable once RSS trait connection is understood (list of RSS files?)
    # self._sub_traits[TraitKey('rss', None, None, None)] = SAMIRowStackedSpectra

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


    @sub_traits.register
    class CatCoordinate(SkyCoordinate):

        trait_type = 'catalog_coordinate'

        @trait_property('float')
        def _ra(self):
            return self._parent_trait.ra()

        @trait_property('float')
        def _dec(self):
            return self._parent_trait.dec()

    @sub_traits.register
    class WCS(WorldCoordinateSystem):

        trait_type = 'wcs'

        @trait_property('string')
        def _wcs_string(self):
            with self._parent_trait.preloaded_context() as pt:
                h = pt.hdu[0].header.copy()
                # The PLATEID header keyword confuses the WCS package,
                # so it must be removed from the header before creating
                # the WCS object
                del h['PLATEID']
                w = wcs.WCS(h)
                return w.to_header_string()

    @sub_traits.register
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

        def preload(self):
            with self._parent_trait.preloaded_context() as pt:
                self._header = pt.hdu[0].header.copy()
                self._header.providence = {"file": pt.hdu.filename, "extension": 0}

        def cleanup(self):
            del self._header

        # trait_properties = [
        #     TraitPropertyFromFitsHeader(name='telescope', header_name='TELESCOP'),
        #     TraitPropertyFromFitsHeader(name='altitude', header_name='ALT_OBS'),
        #     TraitPropertyFromFitsHeader(name='latitude', header_name='LAT_OBS'),
        #     TraitPropertyFromFitsHeader(name='longitude', header_name='LONG_OBS'),
        # ]

        telescope = trait_property_from_fits_header('TELESCOP', 'string', 'telescope')

        altitude = trait_property_from_fits_header('ALT_OBS', 'string', 'altitude')

        latitude = trait_property_from_fits_header('LAT_OBS', 'string', 'latitude')

        longitude = trait_property_from_fits_header('LONG_OBS', 'string', 'longitude')


    @sub_traits.register
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

        def preload(self):
            with self._parent_trait.preloaded_context() as pt:
                self._header = pt.hdu[0].header.copy()

        def cleanup(self):
            del self._header

        detector_id = trait_property_from_fits_header('DETECTOR', 'string', 'detector_id')
        detector_id.short_name = "DETECTOR"

        gain = trait_property_from_fits_header('RO_GAIN', 'string', 'gain')
        gain.short_name = "RO_GAIN"

        read_noise = trait_property_from_fits_header('RO_NOISE', 'string', 'read_noise')
        read_noise.short_name = 'RO_NOISE'

        read_speed = trait_property_from_fits_header('SPEED', 'string', 'read_speed')
        read_speed.short_name = 'SPEED'

        detector_control_software_date = trait_property_from_fits_header('DCT_DATE', 'string', 'detector_control_software_date')
        detector_control_software_date.short_name = 'DCT_DATE'

        detector_control_software_version = trait_property_from_fits_header('DCT_VER', 'string', 'detector_control_software_version')
        detector_control_software_version.short_name = 'DCT_VER'

        read_amplifier = trait_property_from_fits_header('READAMP', 'string', 'read_amplifier')
        read_amplifier.short_name = 'READAMP'


    @sub_traits.register
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

        def preload(self):
            with self._parent_trait.preloaded_context() as pt:
                self._header = pt.hdu[0].header.copy()

        def cleanup(self):
            del self._header

        # @trait_property('string')
        # def instrument_id(self):
        #     with self.parent_trait.preloaded_context() as pt:
        #         return pt.hdu[0].header['INSTRUME']

        instrument_id = trait_property_from_fits_header('INSTRUME', 'string', 'instrument_id')

        spectrograph_arm = trait_property_from_fits_header('SPECTID', 'string', 'spectrograph_arm')

        disperser_id = trait_property_from_fits_header('GRATID', 'string', 'disperser_id')

        disperser_tilt = trait_property_from_fits_header('GRATTILT', 'string', 'disperser_tilt')

        instrument_software_version = trait_property_from_fits_header('TDFCTVER', 'string', 'instrument_software_version')

        instrument_software_date = trait_property_from_fits_header('TDFCTDAT', 'string', 'instrument_software_date')

        dichroic_id = trait_property_from_fits_header('DICHROIC', 'string', 'dichroic_id')



class LZIFUVelocityMap(VelocityMap):

    trait_type = "velocity_map"

    branches_versions = {"lzifu": {"V02"}}

    defaults = DefaultsRegistry(default_branch="lzifu", version_defaults={"lzifu": "V02"})

    def init(self):

        data_product_name = "EmissionLineFits"

        self._lzifu_fits_file = "/".join((
            self.archive.vap_data_path,
            data_product_name,
            data_product_name + self.version,
            "1_comp",
            self.object_id + "_1_comp.fits"))

        if not os.path.exists(self._lzifu_fits_file):
            if os.path.exists(self._lzifu_fits_file + ".gz"):
                self._lzifu_fits_file += ".gz"
            else:
                raise DataNotAvailable("LZIFU file '%s' doesn't exist" % self._lzifu_fits_file)

    def preload(self):
        self._hdu = fits.open(self._lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value().shape

    @property
    def unit(self):
        return units.km / units.s

    @trait_property('float.array')
    def value(self):
        return self._hdu['V'].data[1, :, :]

    @trait_property('float.array')
    def variance(self):
        return self._hdu['V_ERR'].data[1, :, :]


class LZIFUOneComponentLineMap(Image):

    trait_type = 'line_map'

    branches_versions = {"1_comp": {"V02"}}
    defaults = DefaultsRegistry(default_branch="1_comp", version_defaults={"1_comp": "V02"})

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

    qualifier_required = True
    qualifiers = line_name_map.keys()

    def init(self):
        data_product_name = "EmissionLineFits"

        self._lzifu_fits_file = "/".join((
            self.archive.vap_data_path,
            data_product_name,
            data_product_name + self.version,
            "1_comp",
            self.object_id + "_1_comp.fits"))

        if not os.path.exists(self._lzifu_fits_file):
            if os.path.exists(self._lzifu_fits_file + ".gz"):
                self._lzifu_fits_file += ".gz"
            else:
                raise DataNotAvailable("LZIFU file '%s' doesn't exist" % self._lzifu_fits_file)

    def preload(self):
        self._hdu = fits.open(self._lzifu_fits_file)

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
        log.debug("Returning type: %s", type(sigma))
        variance = sigma**2
        return variance


    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu[0].header
        return _wcs_string


    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value


    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUWCS)
LZIFUOneComponentLineMap.set_pretty_name(
    "Line Map",
    OII3726="[OII] (33726A)",
    HBETA='Hβ',
    OIII5007='[OIII] (5007A)',
    OI6300='[OI] (6300A)',
    HALPHA='Hα',
    NII6583='[NII] (6583)',
    SII6716='[SII] (6716)',
    SII6731='[SII] (6731)')

class LZIFURecommendedMultiComponentLineMap(LZIFUOneComponentLineMap):

    branches_versions ={'recom_comp': {"V02"}}

    # Extends 'line_map', so no defaults:
    defaults = DefaultsRegistry(None, {'recom_comp': 'V02'})

    def init(self):
        data_product_name = "EmissionLineFits"

        self._lzifu_fits_file = "/".join((
            self.archive.vap_data_path,
            data_product_name,
            data_product_name + self.version,
            self.branch,
            self.object_id + "_" + self.branch + ".fits"))

        if not os.path.exists(self._lzifu_fits_file):
            if os.path.exists(self._lzifu_fits_file + ".gz"):
                self._lzifu_fits_file += ".gz"
            else:
                raise DataNotAvailable("LZIFU file '%s' doesn't exist" % self._lzifu_fits_file)

    qualifier_required = True
    qualifiers = LZIFUOneComponentLineMap.line_name_map.keys()


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
            return self._parent_trait._wcs_string.value

    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUWCS)
LZIFURecommendedMultiComponentLineMap.set_pretty_name(
    "Line Map",
    OII3726="[OII] (3726Å)",
    HBETA='Hβ',
    OIII5007='[OIII] (5007Å)',
    OI6300='[OI] (6300Å)',
    HALPHA='Hα',
    NII6583='[NII] (6583Å)',
    SII6716='[SII] (6716Å)',
    SII6731='[SII] (6731Å)')

class LZIFUContinuum(SpectralMap):

    trait_type = 'spectral_continuum_cube'

    qualifiers = {'red', 'blue'}

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


class BalmerExtinctionMap(Image, TraitFromFitsFile):
    """Emission extinction map based on the Balmer decrement.

    Extinction maps are calculated using the EmissionLineFitsV01 (which includes
    Balmer flux errors incorporating continuum uncertainties) using the Balmer
    decrement and the Cardelli+89 extinction law, using the code below.

    ```
    balmerdec = ha/hb
    balmerdecerr = balmerdec * sqrt((haerr/ha)^2 + (hberr/hb)^2)
    attencorr = (balmerdec / 2.86)^2.36
    attencorrerr = abs((attencorr * 2.36 * balmerdecerr)/balmerdec)
    ```

    These maps will be in units of “attenuation correction factor” — such that
    you can multiply this map by the Halpha cube to obtain de-extincted Halpha
    cubes.  Note that, when the Balmer decrement is less than 2.86, no
    correction will be applied (attenuation correction factor = 1., error = 0.).

    Errors (1-sigma uncertainties) in the extinction are included as a second
    extension in each file.

    """

    trait_type = 'extinction_map'

    branches_versions = {
        "1_comp": {"V02"},
        "recom_comp": {"V02"}
    }

    defaults = DefaultsRegistry(
        default_branch="recom_comp",
        version_defaults={"1_comp": "V02",
                          "recom_comp": "V02"}
    )

    def fits_file_path(self):
        data_product_name = "ExtinctCorrMaps"

        return "/".join(
            (self.archive.vap_data_path,
             data_product_name,
             data_product_name + self.version,
             self.object_id + "_extinction_" + self.branch + ".fits"))

    value = trait_property_from_fits_data('EXTINCT_CORR', 'float.array', 'value')
    variance = trait_property_from_fits_data('EXTINCT_CORR_ERR', 'float.array', 'value')
BalmerExtinctionMap.set_pretty_name("Balmer Extinction Map")


class SFRMap(Image, TraitFromFitsFile):
    r"""Map of star formation rate based on Hα emission.

    Star formation rate (SFR) map calculated using the EmissionLineFitsV01
    (which includes Balmer flux errors incorporating continuum uncertainties),
    ExtinctionCorrMapsV01, and SFMasksV01.  These are used to calculate star
    formation rate maps (in $M_\odot \, \rm{yr}^{-1} \, \rm{spaxel}^{-1}$) and
    star formation rate surface density maps (in $M_\odot\,\rm{yr}^{-1} \,
    \rm{kpc}^2$) using the code below.  Note that we are using the
    flow-corrected redshifts z_tonry_1 from the SAMI-matched GAMA catalog
    (SAMITargetGAMAregionsV02) to calculate distances.

    ```
    H0 = 70.                                    ;; (km/s)/Mpc, SAMI official cosmology
    distmpc = lumdist(z_tonry,H0=H0)            ;; in Mpc; defaults to omega_m=0.3
    dist = distmpc[0] * 3.086d24                ;; in cm
    kpcperarc = (distmpc[0]/(1+z_tonry[0])^2) * 1000./206265  ;; kiloparsecs per arcsecond
    kpcperpix = kpcperarc*0.5                   ;; half arcsec pixels
    halum = haflux * SFR_classmap * attencorr * 1d-16 * 4*!pi *dist^2   ;; now in erg/s
    sfr = halum * 7.9d-42                       ;; now in Msun/yr, Kennicutt+94
    sfrsd = sfr / kpcperpix^2                   ;; this one in Msun/yr/kpc^2
    ```

    Errors (1-sigma uncertainty) in SFR or SFRSD are included as a second extension in each file.

    A separate map is made for each set of LZIFU emission line fits for each
    galaxy: 1 Gaussian component (`*_1_comp.fits`), 2 Gaussian components
    (`*_2_comp.fits`), 3 Gaussian components (`*_3_comp.fits`), and the recommended
    number of components for each spaxel (`*_recom_comp.fits`).  Each map has
    dimensions of $(50,50,ncomp+1)$.  The slice `[*,*,0]` represents the total star
    formation rate (from the total Halpha flux) summed over all components, and
    the `[*,*,ncomp]` slices represent the star formation rate from each
    individual component.


    ##format: markdown

    """

    trait_type = 'sfr_map'

    branches_versions = {
        "1_comp": {'v01'},
        "recom_comp": {'v01'}
    }

    defaults = DefaultsRegistry(
        default_branch='recom_comp',
        version_defaults={"1_comp": 'v01',
                          "recom_comp": 'v01'}
    )

    def fits_file_path(self):
        data_product_name = "SFRMaps"

        return "/".join(
            (self.archive.vap_data_path,
             data_product_name,
             data_product_name + self.version,
             self.object_id + "_SFR_" + self.branch + ".fits"))

    value = trait_property_from_fits_data('SFR', 'float.array', 'value')
    variance = trait_property_from_fits_data('SFR_ERR', 'float.array', 'value')
SFRMap.set_pretty_name("Star Formation Rate Map")


# class SFRClass(ClassificationMap):
#
#     trait_key = 'sfr_map'
#
#     def fits_file_path(self):
#         return (self.archive._base_directory_path +
#                                 "SFRmaps/" +
#                                 self.object_id + "_SFR_" + self.branch + ".fits")
#
#     value = trait_property_from_fits_data('SFR', 'float.array', 'value')
#     variance = trait_property_from_fits_data('SFR_ERR', 'float.array', 'value')

def update_path(path):
    if path[-1] != "/":
        path = path + "/"
    assert os.path.exists(path)
    return path


class SAMIDR1PublicArchive(Archive):

    cache_dir = "/tmp/fidia-sami_archive/"

    def __init__(self, base_directory_path, master_catalog_name):

        self.base_path = update_path(base_directory_path)
        self.core_data_path = self.base_path + "data_releases/v0.9/"
        self.vap_data_path = self.base_path + "data_products/"
        self.catalog_path = self.base_path + "catalogues/"

        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)

        self._base_directory_path = base_directory_path
        self.master_catalog_path = self.catalog_path + master_catalog_name
        log.debug("master_catalog_path: %s", self.master_catalog_path)

        # Load the master catalog and get the list of IDs this archive will support:
        master_cat = pd.read_table(self.master_catalog_path,
                      delim_whitespace=True,
                      header=None, names=('SAMI_ID', 'red_cube_file'),
                      dtype={'SAMI_ID': str, 'red_cube_file': str}).set_index('SAMI_ID')
        self.contents = master_cat.index


        # The master catalog only has red cube file names, so create a column with blue names as well:
        red_files = master_cat['red_cube_file']
        blue_files = red_files.apply(lambda x: x.replace("red", "blue"))
        master_cat['blue_cube_file'] = blue_files

        self.cube_file_index = master_cat

        log.debug("master cat loaded.")

        self._cubes_directory = self._find_cubes()

        catalog_data_path = (self.catalog_path + "SAMItargetGAMAregions/SAMItargetGAMAregionsV02/" +
                             "SAMItargetGAMAregionsV02.fits")
        with fits.open(catalog_data_path) as m:
            fits_table = m[1].data
            self.tabular_data = pd.DataFrame.from_records(
                fits_table.tolist(),
                columns=map(lambda x: x.name, fits_table.columns))
        self.tabular_data.set_index('CATID', inplace=True)

        # Local cache for traits
        self._trait_cache = dict()

        super(SAMIDR1PublicArchive, self).__init__()


    def _find_cubes(self):

        # Create a set of observing runs in this archive
        self.observing_runs = set()
        for item in os.listdir(self.core_data_path):
            run_match = SAMI_RUN_NAME_RE.match(item)
            if run_match:
                self.observing_runs.add(item)

        # The rest of this function is fairly slow, so we cache the information
        # for future invocations/other processes. This is done in a thread-safe
        # manner.

        cube_data_cache_path = self.cache_dir + self.__class__.__name__ + "cube_file_index.pd.pickle"

        # Grab a file lock so that we will not collide with other processes
        with exclusive_file_lock(cube_data_cache_path):
            if os.path.exists(cube_data_cache_path):
                # Cache already exists.

                # Check if perhaps the cache should be invalidated
                cache_update_time = os.stat(cube_data_cache_path).st_mtime
                mod_update_time = os.stat(__file__).st_mtime
                if mod_update_time < cache_update_time:
                    # Cache is newer than this file, so assume it is valid.
                    cube_directory = pd.read_pickle(cube_data_cache_path)
                    log.info("Existing cache of SAMI cubes found and read in.")
                    return cube_directory
                else:
                    os.remove(cube_data_cache_path)
                    log.info("Existing cache of SAMI cubes found and invalidated.")

            # Cache file doesn't exist or has been invalided so create it.
            log.info("No existing cache of SAMI cubes found---creating new one.")

            # Find all known cube files:
            cube_file_paths = glob(self.core_data_path + "*/cubed/*/*.fits*")
            if len(cube_file_paths) == 0:
                raise ArchiveValidationError("No cube files found for SAMI Archive.")
            cube_directory = []
            for path in cube_file_paths:
                info = cube_info_from_path(path)

                # Only include this file if explicitly listed in the
                # cube_file_index
                print(info['sami_id'], info['color'] + '_cube_file')
                try:
                    catalog_cube_file = self.cube_file_index.loc[info['sami_id'], info['color'] + '_cube_file']
                    assert info['filename'] == catalog_cube_file
                except:
                    log.debug("Cube file '%s' rejected because it is not in the master cat.", info['filename'])
                else:
                    cube_directory.append(info)


            if len(cube_directory) == 0:
                raise ArchiveValidationError("No valid cube file for SAMI Archive.")

            cube_directory = pd.DataFrame(cube_directory)
            log.debug(cube_directory)
            cube_directory.set_index(['sami_id', 'color', 'binning', 'plate_id'], inplace=True)

            # Write out the file (while still under the lock)
            cube_directory.to_pickle(cube_data_cache_path)

        return cube_directory

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
        self.available_traits.register(SAMISpectralCube)
        # Trait 'rss_map' (now a sub-trait of spectral_cube above.)
        # self.available_traits[TraitKey(SAMIRowStackedSpectra.trait_type, None, None, None)] = SAMIRowStackedSpectra

        # LZIFU Items

        self.available_traits.register(LZIFUVelocityMap)

        self.available_traits.register(LZIFUOneComponentLineMap)
        # self.available_traits[TraitKey('line_map', None, "recommended", None)] = LZIFURecommendedMultiComponentLineMap
        self.available_traits.register(LZIFURecommendedMultiComponentLineMap)

        self.available_traits.register(SFRMap)
        self.available_traits.register(BalmerExtinctionMap)

        # self.available_traits[TraitKey('spectral_line_cube', None, None, None)] = LZIFULineSpectrum
        # self.available_traits[TraitKey('spectral_continuum_cube', None, None, None)] = LZIFUContinuum

        if log.isEnabledFor(slogging.DEBUG):
            log.debug("------Available traits--------")
            for key in self.available_traits.get_all_traitkeys():
                log.debug("   Key: %s", key)

        return self.available_traits


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
        self.available_traits.register(SAMISpectralCube)
        # Trait 'rss_map' (now a sub-trait of spectral_cube above.)
        # self.available_traits[TraitKey(SAMIRowStackedSpectra.trait_type, None, None, None)] = SAMIRowStackedSpectra

        # LZIFU Items

        self.available_traits.register(LZIFUVelocityMap)

        self.available_traits.register(LZIFUOneComponentLineMap)
        # self.available_traits[TraitKey('line_map', None, "recommended", None)] = LZIFURecommendedMultiComponentLineMap
        self.available_traits.register(LZIFURecommendedMultiComponentLineMap)

        self.available_traits.register(SFRMap)
        self.available_traits.register(BalmerExtinctionMap)

        # self.available_traits[TraitKey('spectral_line_cube', None, None, None)] = LZIFULineSpectrum
        # self.available_traits[TraitKey('spectral_continuum_cube', None, None, None)] = LZIFUContinuum

        if log.isEnabledFor(slogging.DEBUG):
            log.debug("------Available traits--------")
            for key in self.available_traits:
                log.debug("   Key: %s", key)

        return self.available_traits
