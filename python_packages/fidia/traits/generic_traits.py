from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import ...

# Python Standard Library Imports
import io

# Other Library Imports
from cached_property import cached_property
from PIL import Image as PILImage
from astropy.io import fits, ascii
from astropy import table
from astropy.coordinates import SkyCoord
from astropy import units

# FIDIA Imports
from .base_trait import Trait, TraitCollection
from .trait_utilities import TraitProperty, SubTrait

from fidia.exceptions import *

# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['Image', 'SpectralCube', 'DMU', 'ImageWCS', 'Table',
           'SkyCoordinate',
           'CannonAbundance',
           'EffectiveTemperature', 'LogGravity', 'Metallicity',
           'FITSFile', 'TarFileGroup', 'FitsImageHdu', 'FITSHeader',
           'PixelImage']

class ImageWCS(Trait):
    n_axis = 2
    crpix1 = TraitProperty(dtype=(float, int))
    crpix2 = TraitProperty(dtype=(float, int))
    crval1 = TraitProperty(dtype=(float, int))
    crval2 = TraitProperty(dtype=(float, int))
    cdelt1 = TraitProperty(dtype=(float, int))
    cdelt2 = TraitProperty(dtype=(float, int))
    ctype1 = TraitProperty(dtype=str)
    ctype2 = TraitProperty(dtype=str)



class Image(Trait):
    data = TraitProperty(dtype=(float, int), n_dim=2)
    exposed = TraitProperty(dtype=(float, int), optional=True)
    wcs = SubTrait(ImageWCS, optional=True)

class SkyCoordinate(TraitCollection):

    @cached_property
    def coord(self):
        if hasattr(self, 'ra') and hasattr(self, 'dec'):
            ra_unit = units.Unit(self.get_unit('ra'))
            dec_unit = units.Unit(self.get_unit('dec'))
            frame = getattr(self, 'frame', None)
            return SkyCoord(ra=self.ra*ra_unit, dec=self.dec*dec_unit, frame=frame)


class SpectralCube(Trait):
    data = TraitProperty(dtype=(float, int), n_dim=3)
    spatial_axes = (0, 1)
    wavelength_axis = 2

class CannonAbundance(Trait):
    value = TraitProperty(dtype=(float,), n_dim=0)
    error = TraitProperty(dtype=(float,), n_dim=0)
    flag = TraitProperty(dtype=(int,), n_dim=0)
    norm_depth = TraitProperty(dtype=(float,))
    depth = TraitProperty(dtype=(float,))
    sn = TraitProperty(dtype=(float,))
    chi2 = TraitProperty(dtype=(float,))

class ValueError(Trait):
    value = TraitProperty(dtype=(float, int), n_dim=0)
    error = TraitProperty(dtype=(float, int), n_dim=0)

class ValueOptionalError(Trait):
    value = TraitProperty(dtype=(float, int), n_dim=0)
    error = TraitProperty(dtype=(float, int), n_dim=0, optional=True)

class EffectiveTemperature(ValueOptionalError): pass
class LogGravity(ValueOptionalError): pass
class Metallicity(ValueOptionalError): pass

class StellarProperties(Trait):
    effective_temperature = SubTrait(ValueError)
    log_gravity = SubTrait(ValueError)
    metallicity = SubTrait(ValueError)
    microturbulence = SubTrait(ValueError, optional=True)
    rotational_velocity = SubTrait(ValueError)


class DMU(TraitCollection):
    pass

class Table(TraitCollection):

    def export_as_csv(self, file_handle):

        if self.object_id is not None:
            raise ExportException("Table Trait cannot export as csv for single objects.")

        # Iterate over TraitProperties that are the columns of this Trait, collecting data and names for each column
        column_names = self.dir_trait_properties()
        columns = []
        for n in column_names:
            columns.append(getattr(self, n))

        export_table = table.Table(columns, names=column_names)
        export_table.write(file_handle, format="ascii.csv")

    def export_as_ecsv(self, file_handle):

        if self.object_id is not None:
            raise ExportException("Table Trait cannot export as csv for single objects.")

        # Iterate over TraitProperties that are the columns of this Trait, collecting data and names for each column
        column_names = self.dir_trait_properties()
        columns = []
        for n in column_names:
            columns.append(getattr(self, n))

        export_table = table.Table(columns, names=column_names)

        # Assign Unit and other meta information
        for n in column_names:
            export_table[n].unit = self.get_unit(n)
            export_table[n].description = self.get_short_description(n)

        export_table.write(file_handle, format="ascii.ecsv", delimiter=",")


class FITSFile(TraitCollection):


    def export_as_fits(self, file_handle):

        if self.object_id is None:
            raise ExportException("FITSFile Trait cannot export as fits for multiple objects.")

        hdu_list = fits.HDUList()

        # Iterate over the Image HDUs
        for hdu_name, trait in self.fits_image_hdu.items():
            assert isinstance(trait, FitsImageHdu)
            if hdu_name == 'PRIMARY':
                hdu = fits.PrimaryHDU(trait.data)
            else:
                hdu = fits.ImageHDU(trait.data)

            # Add Header Keywords

            header_trait = trait.fits_header['header']  # type: FITSHeader
            assert isinstance(header_trait, FITSHeader)
            for kw_name in header_trait.dir_trait_properties():
                value = getattr(header_trait, kw_name)
                comment = header_trait.get_short_description(kw_name)
                # unit = header_trait.get_unit(kw_name)
                hdu.header[kw_name] = (value, comment)

            hdu_list.append(hdu)

        # @TODO: Does not handle binary table extensions.

        hdu_list.writeto(file_handle)

class FITSHeader(TraitCollection):
    pass

class FitsImageHdu(TraitCollection):
    data = TraitProperty(dtype=(float, int))
    # header = SubTrait(FITSHeader, optional=True)
    pass


class TarFileGroup(TraitCollection):
    pass

class PixelImage(Trait):
    bytes = TraitProperty(dtype=bytes, n_dim=1)

    @cached_property
    def image(self):
        return PILImage.open(io.BytesIO(self.bytes))

