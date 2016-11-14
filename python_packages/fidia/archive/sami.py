from __future__ import absolute_import, division, print_function, unicode_literals

from glob import glob
import os.path
import datetime
import re
from collections import OrderedDict

import numpy as np

from astropy import wcs
from astropy.io import fits
from astropy import units

import pandas as pd

from cached_property import cached_property

# FIDIA Relative Imports
from fidia import *
from .archive import Archive

from ..utilities import WildcardDictionary, DefaultsRegistry, exclusive_file_lock

#from fidia.traits import TraitKey, trait_property, SpectralMap, Image, VelocityMap, ClassificationMap
from fidia.traits import *
from fidia.traits.trait_property import trait_property_from_fits_header

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

        super(TraitFromFitsFile, self)._post_init()

    def preload(self):
        self._hdu = fits.open(self._fits_file_path)

    def cleanup(self):
        self._hdu.close()

def trait_property_from_fits_data(extension_name, type, name):

    tp = TraitProperty(type=type, name=name)

    tp.fload = lambda self: self._hdu[extension_name].data
    tp.set_short_name(extension_name)

    # # @TODO: Providence information can't get filename currently...
    # tp.providence = "!: FITS-Header {{file: '{filename}' extension: '{extension}' header: '{card_name}'}}".format(
    #     card_name=header_card_name, extension=extension, filename='UNDEFINED'
    # )

    return tp


def file_or_gz_exists(filename):
    if os.path.exists(filename):
        return filename
    if os.path.exists(filename + ".gz"):
        return filename + ".gz"
    return False

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
    r"""Flux cubes from optical integral-field spectroscopy.


    The data cubes
    are taken from version 0.9 of the SAMI reduction pipeline (see [Sharp et al.
    (2014)](http://sami-survey.org/paper/sami-galaxy-survey-resampling-spares-aperture-integral-field-spectroscopy)
    and [Allen et al. (2014)](http://sami-survey.org/paper/early-data-release)
    for details).  There are two cubes for each galaxy, one in the blue, and a
    second in the red.  Note that the red and blue cubes do not overlap in
    wavelength coverage.  Some basic characteristics of the data are given
    below:

    - Blue cube covers ~3700-5700A with a resolution of $R\simeq 1750$ and a
      dispersion of 1.0 Angstrom per pixel.
    - Red cube covers ~6300-7400A with a resolution of $R\simeq 4500$ and a
      dispersion of 0.57 Angstroms per pixel.
    - The cubes are each $50\times 50$ spatial pixels by $2048$ spectral pixels
      with the spatial sampling at 0.5 arcsec.
    - Data are flux calibrated and corrected for telluric absorption to within
      6% in relative flux.
    - The included world coordinate system is centred on catalogue coordinates.
      The acuracy of the astronometry is about 1-2 arcseconds (RMS).
    - Primary HDU contains the data cube: $50\times50$ spatial elements, $2048$
      spectral elements ($50\times50\times2048$).
    - Variance cube ($50\times 50\times 2048$), weight-map cube ($50\times
      50\times 2048$) and covariance hyper-cube ($50\times 50\times 5\times
      5\times n$, where $n$ can vary) are included as extensions.  See below for
      discussion of covariance.

    # Variance and Covariance

    During the reduction, SAMI hexabundles are dithered and resampled onto a regular
    grid, which causes nearby output spaxels to have correlated noise in the spatial
    dimension. This spatial covariance is included in the 'COVAR' extension of the
    cube. (N.B. spectral covariance is small enough to be safely ignored, and is not
    included). Full details of how covariance is handled in SAMI data is included in
    [Sharp et al.
    (2014)](http://sami-survey.org/paper/sami-galaxy-survey-resampling-spares-aperture-integral-field-spectroscopy).

    We leave the choice of how to apply (or otherwise) this covariance
    information to subsequent analysis up to the user, but strongly encourage
    users to read the description in [Sharp et al.
    (2014)](http://sami-survey.org/paper/sami-galaxy-survey-resampling-spares-aperture-integral-field-spectroscopy)
    in detail.

    # Acknowledgements and citations for using the data

    If using SAMI data products, please include this acknowledgement:

    > The SAMI Galaxy Survey is based on observations made at the
    > Anglo-Australian Telescope. The Sydney-AAO Multi-object Integral field
    > spectrograph (SAMI) was developed jointly by the University of Sydney and
    > the Australian Astronomical Observatory. The SAMI input catalogue is based
    > on data taken from the Sloan Digital Sky Survey, the GAMA Survey and the VST
    > ATLAS Survey. The SAMI Galaxy Survey is funded by the Australian Research
    > Council Centre of Excellence for All-sky Astrophysics (CAASTRO), through
    > project number CE110001020, and other participating institutions. The SAMI
    > Galaxy Survey website is http://sami-survey.org/ ."

    Please also cite the following papers:

    - ["The Sydney-AAO Multi-object Integral field spectrograph", Croom et al.
    (2012), MNRAS, 421, 872](http://adsabs.harvard.edu/abs/2012MNRAS.421..872C).
    Instrument description paper.
    - ["The SAMI Galaxy Survey: Target selection and instrument specification",
    Bryant et al., MNRAS 447, 2857 (2015)](http://sami-survey.org/paper/sami-survey-target-selection-and-instrument-specification). Details of survey target selection and revised
    instrument description for upgraded SAMI instrument.
    - ["The SAMI Galaxy Survey: Cubism and covariance, putting round pegs into
    square holes", Sharp et al., MNRAS, 446, 1551
    (2015)](http://sami-survey.org/paper/sami-galaxy-survey-resampling-spares-aperture-integral-field-spectroscopy).
     Data processing pipeline, including flux calibration and drizzle cubing.
    - ["The SAMI Galaxy Survey: Early Data Release", Allen et al., MNRAS, 446, 1567
    (2015)](http://sami-survey.org/paper/early-data-release).  Description of
    early data release, including quality metrics and details of data products.

    # Feedback

    The SAMI Galaxy Survey team welcome feedback on this data release and the
    products contained within it.  If you are actively using the data and/or
    find issues, please contact us on feedback@sami-survey.org.

    """

    sub_traits = TraitRegistry()

    trait_type = 'spectral_cube'
    qualifiers = {'red', 'blue'}

    branches_versions = {('drizzle_05', "Drizzle 0.5\"", "SAMI Drizzle onto 0.5\" grid with drop shrinking"): {"V1"}}
    defaults = DefaultsRegistry(default_branch='drizzle_05',
                                version_defaults={'drizzle_05': 'V1'})

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
        r"""Variance of the flux measurements.

        NOTE: The SAMI Drizzling process introduces considerable co-variance to
        the flux information, which is stored separately.

        """
        # Note: the explicit str conversion is necessary (I suspect a Python 2to3 bug)
        return self.hdu[str('VARIANCE')].data

    @trait_property('float.array')
    def covariance(self):
        r"""Compressed description of the covariance introduced by the drizzling.

        The full covariance matrix for a SAMI cube is both very large and highly
        redundant. Therefore, we calculate and store the covariance only (i) at
        a subset of wavelength slices, and (ii) over small spatial scales only.
        Our testing shows that covariance is only significant over a ~2 spaxel
        radius, therefore, a $5 \times 5$ covariance sub-array is sufficient to
        record all of the covariance for a given pixel. The covariance varies
        significantly along the spectral direction only when the resampling is
        updated to account for the effects of chromatic differential atmospheric
        refraction. Therefore we densely sample only these wavelength slices,
        and sparsely sample slices in between.

        The full $50\times 50 \times 5 \times 5 \times 2048$ covariance
        hyper-cube can be reconstruced from the included covariance data as
        described by [Sharp et al.
        (2014)](http://sami-survey.org/paper/sami-galaxy-survey-resampling-spares-aperture-integral-field-spectroscopy).
        Briefly, missing values in the full hyper-cube should be replaced with
        the nearest measured value along the wavelength axis. Then, each of the
        25 $50\times 50 \times 2048$ cubes (one per element of the $5 \times 5$
        covariance sub-arrays) must be multiplied by the variance cube to
        recover the full covariance. Our testing has shown that this approach
        recovers $> 91\%$ of the covariance in the blue cubes, and $> 97\%$ in
        the red cubes.

        """

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
        # detector_id.set_short_name("DETECTOR")

        gain = trait_property_from_fits_header('RO_GAIN', 'string', 'gain')
        # gain.set_short_name("RO_GAIN")

        read_noise = trait_property_from_fits_header('RO_NOISE', 'string', 'read_noise')
        # read_noise.set_short_name('RO_NOISE')

        read_speed = trait_property_from_fits_header('SPEED', 'string', 'read_speed')
        # read_speed.set_short_name('SPEED')

        detector_control_software_date = trait_property_from_fits_header('DCT_DATE', 'string', 'detector_control_software_date')
        # detector_control_software_date.set_short_name('DCT_DATE')

        detector_control_software_version = trait_property_from_fits_header('DCT_VER', 'string', 'detector_control_software_version')
        # detector_control_software_version.set_short_name('DCT_VER')

        read_amplifier = trait_property_from_fits_header('READAMP', 'string', 'read_amplifier')
        # read_amplifier.set_short_name('READAMP')


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

SAMISpectralCube.set_pretty_name("Spectral Cube")
SAMISpectralCube.set_description("Spatially resolved spectra across the galaxy")

# SAMISpectralCube.value.set_description
# SAMISpectralCube.variance.set_description
# SAMISpectralCube.covariance.set_description
# SAMISpectralCube.weight.set_description
# SAMISpectralCube.total_exposure.set_description
# SAMISpectralCube.cubing_code_version.set_description
# SAMISpectralCube.plate_id.set_description
# SAMISpectralCube.plate_label.set_description

# SAMISpectralCube.CatCoordinate.set_pretty_name()
SAMISpectralCube.CatCoordinate.set_description("Catalog coordinate of the target centre of the SAMI fibre bundle.")

SAMISpectralCube.AAT.altitude.set_description("Altitude of observatory in metres")
SAMISpectralCube.AAT.latitude.set_description("Observatory latitude in degrees")
SAMISpectralCube.AAT.longitude.set_description("Observatory longitude in degrees)")


#         __    ___          __       ___
#    |     / | |__  |  |    |  \  /\   |   /\
#    |___ /_ | |    \__/    |__/ /~~\  |  /~~\
#

branch_lzifu_1_comp = ("1_comp", "LZIFU 1 component", "LZIFU fit with only a single component")
branch_lzifu_m_comp = ('recom_comp', "LZIFU multi component", "LZIFU fits using up to three components")

class LZIFUDataMixin:
    """Mixin class to provide extra properties common to all LZIFU Data."""

    branches_versions = {
        branch_lzifu_1_comp: {'V02'},
        branch_lzifu_m_comp: {'V02'}
    }

    defaults = DefaultsRegistry(default_branch="1_comp",
                                version_defaults={branch_lzifu_1_comp[0]: 'V02', branch_lzifu_m_comp[0]: 'V02'})

    def init(self):
        data_product_name = "EmissionLineFits"

        # Find the filename for this dataset.
        #
        # Several options are tried:
        #   - Bare ID and bare ID with .gz extension
        #   - ID and plate ID combined and the same with .gz

        self._lzifu_fits_file = None

        filepath = "/".join((
            self.archive.vap_data_path,
            data_product_name,
            data_product_name + self.version,
            self.branch,
            self.object_id + "_" + self.branch + ".fits"))

        log.debug("Trying path for LZIFU Data: %s", filepath)

        exists = file_or_gz_exists(filepath)
        if exists:
            # The requested file exists as is
            self._lzifu_fits_file = exists
        else:
            match = re.match(sami_cube_re, self.archive.cube_file_index['red_cube_file'][self.object_id])
            if not match:
                # The given cube_filename is not valid, something is wrong!
                raise DataNotAvailable("The cube filename '%s' cannot be parsed." % self.archive.cube_file_index['red_cube_file'][self.object_id])

            plate_id = match.group('plate_id')
            n_comb = match.group('n_comb')

            filepath = "/".join((
                self.archive.vap_data_path,
                data_product_name,
                data_product_name + self.version,
                self.branch,
                self.object_id + "_" + n_comb + "_" + plate_id + "_" + self.branch + ".fits"))

            log.debug("Trying path for LZIFU Data: %s", filepath)

        exists = file_or_gz_exists(filepath)
        if not self._lzifu_fits_file and exists:
            # Try with the correct plate identifier appended (the case for duplicates)
                self._lzifu_fits_file = exists

        if not self._lzifu_fits_file:
            raise DataNotAvailable("LZIFU file '%s' doesn't exist" % self._lzifu_fits_file)

        log.info("LZIFU Fits file for trait '%s' is '%s'", self, self._lzifu_fits_file)

    def preload(self):
        self._hdu = fits.open(self._lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @trait_property('string')
    def lzifu_version(self):
        return self._hdu[0].header['LZIFUVER']
    lzifu_version.set_short_name('LZIFUVER')
    lzifu_version.set_description("The version of the LZIFU software used in processing.")
    lzifu_version.set_pretty_name("LZIFU Software Version")

    @trait_property('float')
    def lzifu_input_redshift(self):
        return self._hdu[0].header['Z_LZIFU']
    lzifu_input_redshift.set_short_name('Z_LZIFU')
    lzifu_input_redshift.set_description("The starting redshift provided to LZIFU.")
    lzifu_input_redshift.set_pretty_name("LZIFU Input Redshift")


class LZIFUFlag(FlagMap):

    trait_type = 'flags'

    valid_flags = [
        ('BADSKY', "Bad Sky Subtraction"),
        ('BADCONT', "Bad Continuum Fit"),
        ('LOWBALM', "Low Balmer Decrement"),
        ('HIGHBALM', "High Balmer Decrement"),
        ('BADCOMP', "Unknown Number of Componenets"),
        ('NODATA', "No Data")
    ]

    # We don't want all of the mixin class, but we do want the init, data loading and cleanup routines.
    init = LZIFUDataMixin.init
    preload = LZIFUDataMixin.preload
    cleanup = LZIFUDataMixin.cleanup

    @trait_property("int.array")
    def value(self):
        input_data = self._hdu['QF_BINCODE'].data  # type: np.ndarray

        # The array is stored as a unsigned integer array.
        output_data = input_data.astype(np.uint64, casting='safe', copy=False)

        return output_data


class LZIFUVelocityMap(LZIFUDataMixin, VelocityMap):

    trait_type = "velocity_map"

    qualifiers = {'ionized_gas'}

    branches_versions = {
        branch_lzifu_1_comp: {'V02'},
        branch_lzifu_m_comp: {'V02'}
    }
    defaults = DefaultsRegistry(default_branch=branch_lzifu_1_comp[0],
                                version_defaults={branch_lzifu_1_comp[0]: 'V02', branch_lzifu_m_comp[0]: 'V02'})

    # def init(self):
    #
    #     data_product_name = "EmissionLineFits"
    #
    #     self._lzifu_fits_file = "/".join((
    #         self.archive.vap_data_path,
    #         data_product_name,
    #         data_product_name + self.version,
    #         "1_comp",
    #         self.object_id + "_1_comp.fits"))
    #
    #     if not os.path.exists(self._lzifu_fits_file):
    #         if os.path.exists(self._lzifu_fits_file + ".gz"):
    #             self._lzifu_fits_file += ".gz"
    #         else:
    #             raise DataNotAvailable("LZIFU file '%s' doesn't exist" % self._lzifu_fits_file)
    #
    # def preload(self):
    #     self._hdu = fits.open(self._lzifu_fits_file)
    #
    # def cleanup(self):
    #     self._hdu.close()

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
    def error(self):
        return self._hdu['V_ERR'].data[1, :, :]

    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu['V'].header
        return _wcs_string

    #
    # Sub Traits
    #
    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUFlag)


    @sub_traits.register
    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value


class LZIFUVelocityDispersionMap(LZIFUDataMixin, VelocityMap):

    trait_type = "velocity_dispersion_map"

    qualifiers = {'ionized_gas'}

    @property
    def shape(self):
        return self.value().shape

    @property
    def unit(self):
        return units.km / units.s

    @trait_property('float.array')
    def value(self):
        return self._hdu['VDISP'].data[1, :, :]

    @trait_property('float.array')
    def error(self):
        return self._hdu['VDISP_ERR'].data[1, :, :]

    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu['VDISP'].header
        return _wcs_string


    #
    # Sub Traits
    #
    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUFlag)


    @sub_traits.register
    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value


class LZIFUOneComponentLineMap(LZIFUDataMixin, Image):
    r"""Emission line flux map from a single Gaussian fit.

    Documentation from SAMI Team here...

    ##format: markdown
    """


    trait_type = 'line_emission_map'
    branches_versions = {branch_lzifu_1_comp: {"V02"}}
    defaults = DefaultsRegistry(default_branch="1_comp", version_defaults={branch_lzifu_1_comp[0]: "V02"})

    sub_traits = TraitRegistry()

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

    qualifiers = line_name_map.keys()

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
    def error(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[1, :, :]
        log.debug("Returning type: %s", type(sigma))
        return sigma

    # @trait_property('string')
    # def _wcs_string(self):
    #     _wcs_string = self._hdu[0].header
    #     return _wcs_string

    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu[self.line_name_map[self.trait_qualifier]].header
        return _wcs_string


    #
    # Sub Traits
    #
    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUFlag)


    @sub_traits.register
    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value

LZIFUOneComponentLineMap.set_pretty_name(
    "Line Emission Map",
    OII3729="[OII] (3729Å)",
    HBETA='Hβ',
    OIII5007='[OIII] (5007Å)',
    OI6300='[OI] (6300Å)',
    HALPHA='Hα',
    NII6583='[NII] (6583Å)',
    SII6716='[SII] (6716Å)',
    SII6731='[SII] (6731Å)')

class LZIFURecommendedMultiComponentLineMap(LZIFUOneComponentLineMap):
    r"""Emission line flux map from one to three Gaussian fits.

    Documentation from SAMI Team here...

    ##format: markdown
    """
    branches_versions ={branch_lzifu_m_comp: {"V02"}}

    # Extends 'line_map', so no defaults:
    defaults = DefaultsRegistry(None, {branch_lzifu_m_comp[0]: 'V02'})

    # Individual component fluxes released for HALPHA only. See `TotalOnly` class below.
    line_name_map = {
        'HALPHA': 'HALPHA',
    }

    qualifiers = line_name_map.keys()


    def preload(self):
        self._hdu = fits.open(self._lzifu_fits_file)

    @trait_property('float.array')
    def value(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[0, :, :]
        log.debug("Returning type: %s", type(value))
        return value
    value.set_description("Total Line Flux in all components")

    @trait_property('float.array')
    def error(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[0, :, :]
        return sigma
    value.set_description("Variance of Total Line Flux in all components")

    # 1-component
    @trait_property('float.array')
    def comp_1_flux(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[1, :, :]
        return value
    value.set_description("Line Flux in narrowest component")

    @trait_property('float.array')
    def comp_1_error(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[1, :, :]
        return sigma
    value.set_description("Variance of Line Flux in narrowest component")

    @trait_property('float.array')
    def comp_2_flux(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[2, :, :]
        return value
    value.set_description("Line Flux in middle-width component")

    @trait_property('float.array')
    def comp_2_error(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[2, :, :]
        return sigma
    value.set_description("Variance of Line Flux in middle-width component")

    @trait_property('float.array')
    def comp_3_flux(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[3, :, :]
        return value
    value.set_description("Line Flux in broadest component")


    @trait_property('float.array')
    def comp_3_error(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[3, :, :]
        return sigma
    value.set_description("Variance of Line Flux in broadest component")

    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu[self.line_name_map[self.trait_qualifier]].header
        return _wcs_string

    #
    # Sub Traits
    #
    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUFlag)

    @sub_traits.register
    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value

    # End of class LZIFURecommendedMultiComponentLineMap
LZIFURecommendedMultiComponentLineMap.set_pretty_name(
    "Line Emission Map",
    HALPHA='Hα')


class LZIFURecommendedMultiComponentLineMapTotalOnly(LZIFUOneComponentLineMap):
    r"""Total Emission line flux map from one to three Gaussian fits.

    Documentation from SAMI Team here...

    ##format: markdown
    """
    branches_versions = {branch_lzifu_m_comp: {"V02"}}

    # Extends 'line_map', so no defaults:
    defaults = DefaultsRegistry(None, {branch_lzifu_m_comp[0]: 'V02'})

    line_name_map = {
        'OII3726': 'OII3726',
        'OII3729': 'OII3729',
        'HBETA': 'HBETA',
        # Note missing OIII4959, which is fit as 1/3rd of OIII50007
        'OIII5007': 'OIII5007',
        'OI6300': 'OI6300',
        # Note missing NII6548, which is fit as 1/3rd of NII6583
        'NII6583': 'NII6583',
        'SII6716': 'SII6716',
        'SII6731': 'SII6731'
    }

    qualifiers = line_name_map.keys()


    def preload(self):
        self._hdu = fits.open(self._lzifu_fits_file)

    @trait_property('float.array')
    def value(self):
        value = self._hdu[self.line_name_map[self.trait_qualifier]].data[0, :, :]
        log.debug("Returning type: %s", type(value))
        return value
    value.set_description("Total Line Flux in all components")

    @trait_property('float.array')
    def error(self):
        sigma = self._hdu[self.line_name_map[self.trait_qualifier] + '_ERR'].data[0, :, :]
        return sigma
    value.set_description("Variance of Total Line Flux in all components")


    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu[self.line_name_map[self.trait_qualifier]].header
        return _wcs_string

    #
    # Sub Traits
    #
    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUFlag)

    @sub_traits.register
    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value

LZIFURecommendedMultiComponentLineMapTotalOnly.set_pretty_name(
    "Line Emission Map",
    OII3729="[OII] (3729Å)",
    HBETA='Hβ',
    OIII5007='[OIII] (5007Å)',
    OI6300='[OI] (6300Å)',
    NII6583='[NII] (6583Å)',
    SII6716='[SII] (6716Å)',
    SII6731='[SII] (6731Å)')


class LZIFUCombinedFit(SpectralMap):

    trait_type = 'spectral_fit_cube'

    qualifiers = {'red', 'blue'}

    branches_versions = {
        branch_lzifu_1_comp: {'V02'},
        branch_lzifu_m_comp: {'V02'}
    }
    defaults = DefaultsRegistry(default_branch=branch_lzifu_1_comp[0],
                                version_defaults={branch_lzifu_1_comp[0]: 'V02', branch_lzifu_m_comp[0]: 'V02'})

    def init(self):
        data_product_name = "EmissionLineFits"

        self._lzifu_fits_file = "/".join((
            self.archive.vap_data_path,
            data_product_name,
            data_product_name + self.version,
            self.branch,
            self.object_id + "_" + self.branch + ".fits"))

        log.debug("LZIFU Fits file for trait '%s' is '%s'", self, self._lzifu_fits_file)

        if not os.path.exists(self._lzifu_fits_file):
            if os.path.exists(self._lzifu_fits_file + ".gz"):
                self._lzifu_fits_file += ".gz"
            else:
                raise DataNotAvailable("LZIFU file '%s' doesn't exist" % self._lzifu_fits_file)

        # Determine which colour:
        if self.trait_qualifier == "blue":
            self._color = "B"
        elif self.trait_qualifier == "red":
            self._color = "R"
        else:
            raise UnknownTrait("'%s' is not a valid qualifier for '%s'", (self.trait_qualifier, self.trait_type))

    def preload(self):
        self._hdu = fits.open(self._lzifu_fits_file)

    def cleanup(self):
        self._hdu.close()

    @property
    def shape(self):
        return self.value().shape

    @trait_property('float.array')
    def value(self):
        return self._hdu[self._color + '_CONTINUUM'].data + self._hdu[self._color + '_LINE'].data

    @trait_property('float.array')
    def error(self):
        raise DataNotAvailable("No error data available for LZIFU combined spectral fit.")

    @trait_property('string')
    def _wcs_string(self):
        _wcs_string = self._hdu[self._color + '_CONTINUUM'].header
        return _wcs_string


    #
    # Sub Traits
    #
    sub_traits = TraitRegistry()
    sub_traits.register(LZIFUFlag)

    @sub_traits.register
    class LZIFUWCS(WorldCoordinateSystem):
        @trait_property('string')
        def _wcs_string(self):
            return self._parent_trait._wcs_string.value


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
    def error(self):
        raise DataNotAvailable("No error data available for LZIFU continuum spectral fit.")

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
    def error(self):
        raise DataNotAvailable("No error data available for LZIFU emission spectral fit.")


#     __   ___  __                          ___          __   __
#    /__` |__  |__)    \  /  /\  |    |  | |__      /\  |  \ |  \
#    .__/ |    |  \     \/  /~~\ |___ \__/ |___    /~~\ |__/ |__/
#
#    Value added products from Anne's star-formation rate estimates.
#
#    There are three main products here:
#       - SFR Maps
#       - SF Classifications
#       - Balmer Extinction estimates


class BalmerExtinctionMap(Image, TraitFromFitsFile):
    r"""Emission extinction map based on the Balmer decrement.

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
        branch_lzifu_1_comp: {'V02'},
        branch_lzifu_m_comp: {'V02'}
    }
    defaults = DefaultsRegistry(default_branch=branch_lzifu_1_comp[0],
                                version_defaults={branch_lzifu_1_comp[0]: 'V02', branch_lzifu_m_comp[0]: 'V02'})

    def fits_file_path(self):
        data_product_name = "ExtinctCorrMaps"

        return "/".join(
            (self.archive.vap_data_path,
             data_product_name,
             data_product_name + self.version,
             self.object_id + "_extinction_" + self.branch + ".fits"))

    value = trait_property_from_fits_data('EXTINCT_CORR', 'float.array', 'value')
    error = trait_property_from_fits_data('EXTINCT_CORR_ERR', 'float.array', 'value')
BalmerExtinctionMap.set_pretty_name("Balmer Extinction Map")


class SFRMap(Image, TraitFromFitsFile):
    r"""Map of star formation rate based on Hα emission.

    Star formation rate (SFR) map calculated using the EmissionLineFitsV01
    (which includes Balmer flux errors incorporating continuum uncertainties),
    ExtinctionCorrMapsV01, and SFMasksV01.  These are used to calculate star
    formation rate maps (in $M_\odot \, \rm{yr}^{-1} \, \rm{spaxel}^{-1}$).
    Note that we are using the flow-corrected redshifts z_tonry_1 from the
    SAMI-matched GAMA catalog (SAMITargetGAMAregionsV02) to calculate distances.

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

    Errors (1-sigma uncertainty) in SFR are also included.

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
        branch_lzifu_1_comp: {'V02'},
        branch_lzifu_m_comp: {'V02'}
    }
    defaults = DefaultsRegistry(default_branch=branch_lzifu_1_comp[0],
                                version_defaults={branch_lzifu_1_comp[0]: 'V02', branch_lzifu_m_comp[0]: 'V02'})

    def fits_file_path(self):
        data_product_name = "SFRMaps"

        return "/".join(
            (self.archive.vap_data_path,
             data_product_name,
             data_product_name + self.version,
             self.object_id + "_SFR_" + self.branch + ".fits"))

    value = trait_property_from_fits_data('SFR', 'float.array', 'value')
    value.set_description(r"Star formation rate maps (in $M_\odot \, \rm{yr}^{-1} \, \rm{spaxel}^{-1}$)")
    error = trait_property_from_fits_data('SFR_ERR', 'float.array', 'error')
    error.set_description(r"Errors (1-sigma uncertainty) in SFR.")

SFRMap.set_pretty_name("Star Formation Rate Map")


class EmissionClass(ClassificationMap, TraitFromFitsFile):
    r"""Classification of emission in each spaxel as star forming or as other ionisation mechanisms.

    We classify each spaxel using (when possible) [OIII]/Hβ, [NII]/Hα,
    [SII]/Hα, and [OI]/Hα flux ratios from EmissionLineFitsV01 to
    determine whether the emission lines are dominated by photoionization from
    HII regions or other sources like AGN or shocks, using the BPT/VO87
    diagnostic diagrams and dividing lines from Kewley et al. 2006.  We only
    classify spaxels with ratios that have a signal-to-noise ratio of at least
    5.

    We additionally add a likely classification of "star-forming" to spaxels
    with $\log(\rm{[NII]}/\rm{Hα}) < -0.4$ without an [OIII] detection.

    Classifications are stored in the map as an integer with the following definitions:

    | Pixel Value | Classification |
    | ------------|----------------|
    |   0         |  No data       |
    |   1         | star formation dominates the emission in all available line ratios |
    |   2         | other ionization mechanisms dominate |

    We note that these classifications are done only using the *total emission
    line flux* in a spectrum.  Thus, for spectra which contain 2 or 3 components,
    we classify the total emission in that spaxel, not the individual
    components.

    """

    trait_type = 'emission_classification_map'

    branches_versions = {
        branch_lzifu_1_comp: {'V02'},
        branch_lzifu_m_comp: {'V02'}
    }
    defaults = DefaultsRegistry(default_branch=branch_lzifu_1_comp[0],
                                version_defaults={branch_lzifu_1_comp[0]: 'V02', branch_lzifu_m_comp[0]: 'V02'})

    class_remap = {
        0: "No Data",
        1: "Star formation",
        2: "Other ionisation mechanisms"}

    def fits_file_path(self):
        data_product_name = "SFMasks"

        return "/".join(
            (self.archive.vap_data_path,
             data_product_name,
             data_product_name + self.version,
             self.object_id + "_SFMask_" + self.branch + ".fits"))

    @trait_property("int.array")
    def value(self):
        input_data = self._hdu[1].data

        # Change the input array into an integer array for storage.
        class_remap = {
            np.nan: 0,
            1.0: 1,
            0.0: 2}
        output_data = np.empty(input_data.shape, dtype=np.int)
        output_data[:] = -1
        for key in class_remap:
            if key is np.nan:
                # Must use alternate logic for nans
                output_data[np.isnan(input_data)] = class_remap[key]
            output_data[input_data == key] = class_remap[key]

        if np.count_nonzero(output_data == -1) > 0:
            # For some reason, not all pixels have matched the categories.
            raise Exception("Data corruption in '%s'" % self)


        return output_data

    @property
    def shape(self):
        return self.value().shape

EmissionClass.set_pretty_name("Emission Classification Map")




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
            self.tabular_data['CATID'] = self.tabular_data['CATID'].astype(str)
            self.tabular_data['name'] = self.tabular_data['name'].str.decode('utf8')
        self.tabular_data.set_index('CATID', inplace=True)
        log.debug("tabular_data columns: %s", self.tabular_data.columns)

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
                except:
                    log.debug("Cube file '%s' rejected because it is not in the master cat.", info['filename'])
                else:
                    if info['filename'] == catalog_cube_file:
                        cube_directory.append(info)
                    elif info['filename'] + ".gz" == catalog_cube_file:
                        cube_directory.append(info)
                    else:
                        log.debug("Cube file '%s' rejected because it is not in the master cat.", info['filename'])

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


    feature_catalog_data = [
        TraitPath("iau_id"),
        TraitPath("catalog_coordinate", trait_property='_ra'),
        TraitPath("catalog_coordinate", trait_property='_dec'),
        TraitPath("redshift:helio"),
        TraitPath("M_r-auto"),
        TraitPath("mass")
    ]

    def define_available_traits(self):

        # Trait 'spectral_cube'
        self.available_traits.register(SAMISpectralCube)
        # Trait 'rss_map' (now a sub-trait of spectral_cube above.)
        # self.available_traits[TraitKey(SAMIRowStackedSpectra.trait_type, None, None, None)] = SAMIRowStackedSpectra

        #  __       ___            __   __      __   __   __   __   ___  __  ___    ___  __
        # /  `  /\   |   /\  |    /  \ / _`    |__) |__) /  \ |__) |__  |__)  |  | |__  /__`
        # \__, /~~\  |  /~~\ |___ \__/ \__>    |    |  \ \__/ |    |___ |  \  |  | |___ .__/

        sami_gama_catalog_branch = ('sami_gama', 'SAMI-GAMA', 'SAMI-GAMA Target Catalog')

        # name (IAU Identifier)
        iau_name = catalog_trait(Measurement, 'iau_id',
                                OrderedDict([('value', self.tabular_data['name'])]))
        iau_name.set_pretty_name(r"IAU Identifier")
        iau_name.set_description("IAU format object name")
        iau_name.branches_versions = {('iau', "IAU Standard"): {"V02"}}
        self.available_traits.register(iau_name)
        self.available_traits.change_defaults('iau_id', DefaultsRegistry(default_branch='iau'))
        del iau_name

        # RA and DEC
        cat_coord = catalog_trait(SkyCoordinate, 'catalog_coordinate',
                                  OrderedDict([('_ra', self.tabular_data['RA']),
                                               ('_dec', self.tabular_data['Dec'])]))
        cat_coord.set_description("J2000 Right Ascension and Declination")
        cat_coord.set_documentation(r"Source: GAMA catalogs [InputCatv29 TilingCatv29 RA/DEC]")
        cat_coord.set_pretty_name("Catalog Coordinate")
        cat_coord.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        self.available_traits.register(cat_coord)
        del cat_coord
        self.available_traits.change_defaults('catalog_coordinate', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))

        # r_petro
        r_petro = catalog_trait(Measurement, 'm_r-petrosian',
                                OrderedDict([('value', self.tabular_data['r_petro']),
                                             ('unit', units.mag)]))
        r_petro.set_pretty_name(r"r-band Magnitude", petrosian="Petrosian")
        r_petro.set_description("Extinction-corrected SDSS DR7 Petrosian mag")
        r_petro.set_documentation(r"Source: GAMA catalogs [InputCatv29 TilingCatv29 R_PETRO]")
        r_petro.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        self.available_traits.register(r_petro)
        self.available_traits.change_defaults('m_r-petrosian', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))
        del r_petro

        # r_auto
        r_auto = catalog_trait(Measurement, 'm_r-auto',
                                OrderedDict([('value', self.tabular_data['r_auto']),
                                             ('unit', units.mag)]))
        r_auto.set_pretty_name(r"r-band Mag", auto="Auto")
        r_auto.set_description("Extinction-corrected Kron magnitude (r band)")
        r_auto.set_documentation("""The magntidues in the GAMA table ApMatchedCatv03 are not extinction-corrected,
                                    so we corrected them using extinction values from GalacticExtinctionv02.

                                    Source: GAMA catalogs [ApMatchedPhotomv03 ApMatchedCatv03 MAG_AUTO_R - A_r]""",
                                 format='markdown')
        r_auto.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        self.available_traits.register(r_auto)
        del r_auto
        self.available_traits.change_defaults('m_r-auto', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))

        # z_helio
        redshift = catalog_trait(Redshift, 'redshift', OrderedDict([('value', self.tabular_data['z_helio'])]))
        redshift.branches_versions = {('helio', "Heliocentric", "Redshift in the heliocentric frame"): {"V02"}}
        redshift.set_description("Heliocentric redshift  [LocalFlowCorrectionv08 DistancesFramesv08 Z_HELIO]")
        self.available_traits.register(redshift)
        del redshift

        # z_tonry
        redshift_tonry = catalog_trait(Redshift, 'redshift', OrderedDict([('value', self.tabular_data['z_tonry'])]))
        redshift_tonry.branches_versions = {('tonry', "Flow Corrected", "Flow corrected redshift using Tonry model"): {"V02"}}
        redshift_tonry.set_description("Flow-corrected redshift using Tonry model")
        redshift_tonry.set_documentation(
            r"""Source: GAMA catalogs [LocalFlowCorrectionv08 DistancesFramesv08 Z_TONRY]

            The GAMA source catalogue contains the following notes regarding
            this column "This column provides a redshift corrected for peculiar
            velocities due to local flows, using the Tonry et~al. (2000, ApJ,
            530, 625) flow model described in the Appendix of that paper. Note
            there are triple-valued solutions of $z_\textrm{cmb} \rightarrow z_\textrm{tonry}$ over a small
            range in G12 (near Virgo cluster), here the average distance is use
            The solution is tapered to $z_\textrm{cmb}$ from $z_\textrm{cmb}=0.02$ to $z_\textrm{cmb}=0.03$. Thus
            $z_\textrm{tonry} = z_\textrm{cmb}$ at $z_\textrm{cmb} > 0.03$. $z_\textrm{tonry}$ is close to but not exactly
            equal to $z_\textrm{lg}$ (Local Group frame redshift) at $< \sim10$ Mpc."
            """,
            format='latex'
        )
        self.available_traits.register(redshift_tonry)
        del redshift_tonry

        self.available_traits.change_defaults('redshift', DefaultsRegistry(default_branch='helio'))


        # M_r
        r_abs = catalog_trait(Measurement, 'M_r-auto',
                                OrderedDict([('value', self.tabular_data['M_r']),
                                             ('unit', units.mag)]))
        r_abs.set_pretty_name(r"Absolute r-band Mag", auto="Auto")
        r_abs.set_description(r"Absolute magnitude in restframe r-band from SED fits")
        r_abs.set_documentation(
            r"""Source: GAMA catalogs [StellarMassesv08 absmag_r]

            The GAMA source catalogue contains the following notes regarding
            this column which must be taken into account before using $M_r$ for
            science analysis "The values in this table are based on aperture
            (AUTO) photometry, which may miss a significant fraction of a
            galaxy's light. Make sure you understand the need for and meaning of
            the quantity <fluxscale>, which is described under 'based on matched
            aperture photometry' [in the StellarMassesv08 notes file]."

            """,
            format='markdown')
        r_abs.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        r_abs.defaults = DefaultsRegistry(sami_gama_catalog_branch[0], {sami_gama_catalog_branch[0]: "V02"})
        self.available_traits.register(r_abs)
        del r_abs

        # r_e: effective radius
        r_e = catalog_trait(Measurement, 'effective_radius',
                            OrderedDict([('value', self.tabular_data['mu_within_1re']),
                                         ('unit', units.arcsecond)]))
        r_e.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        r_e.defaults = DefaultsRegistry(sami_gama_catalog_branch[0], {sami_gama_catalog_branch[0]: "V02"})
        r_e.set_pretty_name(r"Effective Radius")
        r_e.set_description(r"Effective radius in r-band (hl rad) (semi-major)")
        r_e.set_documentation(r"Source: GAMA catalogs [SersicPhotometryv07 SersicCatAllv07 GAL_RE_R]")
        self.available_traits.register(r_e)
        del r_e

        # mu_within_1re
        surf_bright = catalog_trait(Measurement, 'surface_brightness',
                            OrderedDict([('value', self.tabular_data['mu_within_1re']),
                                         ('unit',  units.mag/units.arcsec**2)]))
        surf_bright.branches_versions = {('central', "Central", "Surface Brightness within $1R_e$"): {"V02"}}
        surf_bright.set_description(r"Effective r-band surface brightness within r_e")
        surf_bright.set_documentation(r"Source: GAMA catalogs [SersicPhotometryv07 SersicCatAllv07 GAL_MU_E_AVG_R]")
        self.available_traits.register(surf_bright)
        del surf_bright

        # mu_1re
        surf_bright = catalog_trait(Measurement, 'surface_brightness',
                            OrderedDict([('value', self.tabular_data['mu_1re']),
                                         ('unit', units.mag/units.arcsec**2)]))
        surf_bright.branches_versions = {('1re', "1R_e", "Surface Brightness at $1R_e$"): {"V02"}}
        surf_bright.set_description(r"Effective r-band surface brightness at r_e")
        surf_bright.set_documentation(r"Source: GAMA catalogs [SersicPhotometryv07 SersicCatAllv07 GAL_MU_E_R]")
        self.available_traits.register(surf_bright)
        del surf_bright

        # mu_2re
        surf_bright = catalog_trait(Measurement, 'surface_brightness',
                            OrderedDict([('value', self.tabular_data['mu_2re']),
                                         ('unit',  units.mag/units.arcsec**2)]))
        surf_bright.branches_versions = {('2re', "2R_e", "Surface Brightness at $2R_e$"): {"V02"}}
        surf_bright.set_description(r"Effective r-band surface brightness at 2r_e")
        surf_bright.set_documentation(r"Source: GAMA catalogs [SersicPhotometryv07 SersicCatAllv07 GAL_MU_E_2R]")
        self.available_traits.register(surf_bright)
        del surf_bright

        log.debug("Setting surface_brightness default.")
        self.available_traits.change_defaults('surface_brightness', DefaultsRegistry(default_branch='central'))
        log.debug(self.available_traits._trait_name_defaults['surface_brightness']._default_branch)


        # ellip
        ellip = catalog_trait(MorphologicalMeasurement, 'ellipticy-r_band',
                              OrderedDict([('value', self.tabular_data['ellip'])]))  # type: MorphologicalMeasurement
        ellip.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        ellip.set_pretty_name("Ellipticity", r_band="r-band")
        ellip.set_description("Ellipticity from r-band Sersic fits")
        ellip.set_documentation(r"Source: GAMA catalogs [SersicPhotometryv07 SersicCatAllv07 GAL_ELLIP_R]")
        self.available_traits.register(ellip)
        del ellip

        self.available_traits.change_defaults('ellipticy-r_band', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))


        # pa
        pa = catalog_trait(MorphologicalMeasurement, 'position_angle-r_band',
                           OrderedDict([('value', self.tabular_data['PA']),
                                        ('unit', units.deg)]))  # type: MorphologicalMeasurement
        pa.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        pa.set_pretty_name("Position Angle", r_band="r-band")
        pa.set_description("Position angle from r-band Sersic fits")
        pa.set_documentation(r"Source: GAMA catalogs [SersicPhotometryv07 SersicCatAllv07 GAL_PA_R]")
        self.available_traits.register(pa)
        del pa

        self.available_traits.change_defaults('position_angle-r_band', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))


        # logmstar_proxy
        stellar_mass = catalog_trait(Measurement, 'mass',
                           OrderedDict([('value', self.tabular_data['logmstar_proxy']),
                                        ('unit', units.dex(units.solMass))]))  # type: Measurement
        stellar_mass.branches_versions = {('proxy', "Stellar Mass Proxy", ""): {"V02"}}
        stellar_mass.set_pretty_name("Stellar Mass")
        stellar_mass.set_description("Stellar mass proxy (see Bryant et al. 2015) (units of log(Mstar/Msun))")
        stellar_mass.set_documentation(
            r"""The stellar mass values in this catalogue are not based on SED fitting, but are
            proxies for stellar mass based on colours to aid the selection of galaxies for
            the SAMI survey.  We calculated the stellar mass proxy for the SAMI survey from
            observed-frame Milky Way-extinction-corrected apparent magnitudes (\emph{g} and \emph{i}),
            and limited the colours to reasonable values of $-0.2 < g - i < 1.6$. The
            relation is:

            \begin{align}
            \log \left( \frac{M_*}{M_\cdot}\right) = -0.4i + 0.4D - \log(1.0 + z) + (1.2117 - 0.5893z) + (0.7106 - 0.1467z) \times (g i)
            \end{align}

            where D is the distance modulus.  For SED-based stellar masses,
            please refer to the GAMA catalogue StellarMassesv08 with careful
            reference to the `fluxscale' correction discussed in the notes file
            that accompanies that catalogue.

            """,
            format='latex')
        self.available_traits.register(stellar_mass)
        self.available_traits.change_defaults('mass', DefaultsRegistry(default_branch='proxy'))
        del stellar_mass

        g_i = catalog_trait(Measurement, 'g_i',
                           OrderedDict([('value', self.tabular_data['g_i'])]))  # type: Measurement
        g_i.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        g_i.set_pretty_name(r"Kron Colour")
        g_i.set_description(r"Kron colour (aperture-matched based on r-band), extinction corrected.")
        g_i.set_documentation(
            r"""Source: GAMA catalogs [ApMatchedPhotomv03 ApMatchedCatv03 MAG_AUTO_G -MAG_AUTO_I -A_g +A_i]

            NOTE: The magntidues in the GAMA table ApMatchedCatv03 are not
            extinction-corrected, so we corrected them using extinction values
            from GalacticExtinctionv02
            """
        )
        self.available_traits.register(g_i)
        del g_i

        self.available_traits.change_defaults('g_i', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))


        A_g = catalog_trait(Measurement, 'A_gal-g_band',
                            OrderedDict([('value', self.tabular_data['A_g'])]))  # type: Measurement
        A_g.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        A_g.set_pretty_name("Galactic extinction", g_band='g-band')
        A_g.set_description("Galactic extinction in SDSS g band.")
        A_g.set_documentation("""Source: GAMA catalogs [InputCatv29 GalacticExtinctionv02 A_g]""")
        self.available_traits.register(A_g)
        del A_g

        self.available_traits.change_defaults('A_gal-g_band', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))


        surv_sami = catalog_trait(Measurement, 'priority_class',
                            OrderedDict([('value', self.tabular_data['SURV_SAMI'])]))  # type: Measurement
        # @TODO: Change to Classification type or similar as appropriate.
        surv_sami.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        surv_sami.set_description("Sample priority class")
        surv_sami.set_documentation(r"""Classifications: primary = 8; high-mass fillers = 4; remaining fillers = 3.""")
        self.available_traits.register(surv_sami)
        del surv_sami

        self.available_traits.change_defaults('priority_class', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))


        bad_class = catalog_trait(Measurement, 'visual_class',
                            OrderedDict([('value', self.tabular_data['BAD_CLASS'])]))  # type: Measurement
        # @TODO: Change to Classification type or similar as appropriate.
        bad_class.branches_versions = {sami_gama_catalog_branch: {"V02"}}
        bad_class.set_description("Classification based on visual inspection (see Bryant et al. 2015).")
        bad_class.set_documentation(
            r"""The BAD\_CLASS flag measures the visual classification as follows:
            \begin{description}
                \item[0] object is OK;
                \item[1] nearby bright star;
                \item[2] target is a star;
                \item[3] subcomponent of a galaxy;
                \item[4] very large, low redshift galaxy;
                \item[5] needs re-centring;
                \item[6] poor redshift;
                \item[7] other problems,
                \item[8] smaller component of a close pair of galaxies, where the second
                     galaxy is outside of the bundle radius. Only objects with BAD\_CLASS =
                    0, 5 or 8 will be in the sample that may be observed.
            \end{description}

            """,
            format='latex'
        )
        self.available_traits.register(bad_class)
        del bad_class

        self.available_traits.change_defaults('visual_class', DefaultsRegistry(default_branch=sami_gama_catalog_branch[0]))



        #      __    ___          __       ___
        # |     / | |__  |  |    |  \  /\   |   /\
        # |___ /_ | |    \__/    |__/ /~~\  |  /~~\


        self.available_traits.register(LZIFUVelocityMap)
        self.available_traits.register(LZIFUVelocityDispersionMap)
        self.available_traits.register(LZIFUOneComponentLineMap)
        self.available_traits.register(LZIFUCombinedFit)
        # self.available_traits[TraitKey('line_map', None, "recommended", None)] = LZIFURecommendedMultiComponentLineMap
        self.available_traits.register(LZIFURecommendedMultiComponentLineMap)
        self.available_traits.register(LZIFURecommendedMultiComponentLineMapTotalOnly)

        self.available_traits.register(SFRMap)
        self.available_traits.register(BalmerExtinctionMap)

        # self.available_traits[TraitKey('spectral_line_cube', None, None, None)] = LZIFULineSpectrum
        # self.available_traits[TraitKey('spectral_continuum_cube', None, None, None)] = LZIFUContinuum

        self.available_traits.register(EmissionClass)

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










#
# LZIFUOneComponentLineMap.set_pretty_name(
#     "Line Map",
#     OII3726="[OII] (33726A)",
#     HBETA='Hβ',
#     OIII5007='[OIII] (5007A)',
#     OI6300='[OI] (6300A)',
#     HALPHA='Hα',
#     NII6583='[NII] (6583)',
#     SII6716='[SII] (6716)',
#     SII6731='[SII] (6731)')
#
# LZIFURecommendedMultiComponentLineMap.set_pretty_name(
#     "Line Map",
#     OII3726="[OII] (3726Å)",
#     HBETA='Hβ',
#     OIII5007='[OIII] (5007Å)',
#     OI6300='[OI] (6300Å)',
#     HALPHA='Hα',
#     NII6583='[NII] (6583Å)',
#     SII6716='[SII] (6716Å)',
#     SII6731='[SII] (6731Å)')

BalmerExtinctionMap.set_pretty_name("Balmer Extinction Map")
SFRMap.set_pretty_name("Star Formation Rate Map")

