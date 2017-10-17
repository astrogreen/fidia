from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import ...

# Python Standard Library Imports
import io

# Other Library Imports
from cached_property import cached_property
from PIL import Image as PILImage
from astropy.io import fits

# FIDIA Imports
from .base_trait import Trait, TraitCollection
from .trait_utilities import TraitProperty, SubTrait

# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['Image', 'SpectralCube', 'DMU', 'ImageWCS', 'Table',
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

class SpectralCube(Trait):
    data = TraitProperty(dtype=(float, int), n_dim=3)
    spatial_axes = (0, 1)
    wavelength_axis = 2

class DMU(TraitCollection):
    pass

class Table(TraitCollection):

    pass


class FITSFile(TraitCollection):


    def export_as_fits(self, file_handle):

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

