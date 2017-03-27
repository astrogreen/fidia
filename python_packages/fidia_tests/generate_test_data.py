from __future__ import absolute_import, division, print_function, unicode_literals

import random
import os

import numpy as np

from astropy.io import fits
from astropy.wcs import WCS

class TestData:

    def __init__(self, size):
        self.object_ids = ["Gal{}".format(i+1) for i in range(size)]

    def data(self):
        # An empty iterator (from http://stackoverflow.com/a/26271684/1970057)
        return iter(())

    def metadata(self, object_id):
        # An empty iterator
        return iter(())


class CatalogTable(TestData):

    def __init__(self):
        pass

def checkdir(output_directory, filename):
    path = os.path.join(output_directory, filename)
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)

def write_to_single_extension_fits(test_data, output_directory, filename_pattern):
    # type: (TestData, str, str) -> None
    for objid, datum in zip(test_data.object_ids, test_data.data()):
        pdu = fits.PrimaryHDU(datum.T)

        meta = test_data.metadata(objid)
        for key in meta:
            pdu.header[key] = meta[key]
        if hasattr(test_data, 'wcs'):
            w = test_data.wcs(objid)  # type: WCS
            pdu.header.extend(w.to_header())
        filename = filename_pattern.format(object_id=objid)
        checkdir(output_directory, filename)
        pdu.writeto(os.path.join(output_directory, filename))


class SimpleImage(TestData):

    def data(self):
        for objid in self.object_ids:
            yield np.random.random((200, 200))

    def metadata(self, object_id):
        random.seed(hash(object_id))
        return {
            "TELESCOP": ("Anglo-Australian Telescope", "Telescope"),
            "OBJECT": (object_id, "Name of the galaxy"),
            "EXPOSED": (random.choice([3600, 2400, 3500]), "Exposure time")
        }


class SpectralCube(TestData):

    def __init__(self, size, wave_start, wave_end, sampling):
        super(SpectralCube, self).__init__(size)

        self.wavescale = np.linspace(wave_start, wave_end, (wave_end - wave_start)//sampling)
        self.wave_sampling = sampling

    def data(self):
        for objid in self.object_ids:
            yield np.random.random((20, 30, len(self.wavescale)))

    def metadata(self, object_id):
        random.seed(hash(object_id))
        return {
            "TELESCOP": ("Anglo-Australian Telescope", "Telescope"),
            "OBJECT": (object_id, "Name of the galaxy"),
            "EXPOSED": (random.choice([3600, 2400, 3500]), "Exposure time")
        }

    def wcs(self, object_id):
        w = WCS(naxis=3)
        w.wcs.crpix = [10, 15, 1]
        w.wcs.crval = np.random.uniform(-10, 10, 3)
        w.wcs.crval[2] = self.wavescale[0]
        w.wcs.cdelt = [1/3600, 1/3600, self.wave_sampling]
        w.wcs.ctype = ['RA---TAN', 'DEC--TAN', 'WAVELEN']
        return w

def generate_simple_dataset(output_directory, size):

    # Create an image of each object at "Gal1/Gal1_red_image.fits"
    write_to_single_extension_fits(SimpleImage(size), output_directory, "{object_id}/{object_id}_red_image.fits")

    # Create a spectral cube
    write_to_single_extension_fits(SpectralCube(size, 3400, 3600, 1.34), output_directory, "{object_id}/{object_id}_spec_cube.fits")


if __name__ == '__main__':
    import sys
    if type(sys.argv[1]) is str:
        generate_simple_dataset(sys.argv[1], 5)