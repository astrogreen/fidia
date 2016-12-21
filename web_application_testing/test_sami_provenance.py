import pytest

import tempfile

import requests
from astropy.io import fits

from numpy.testing import assert_array_equal

from urllib.request import urlretrieve


SHORT_TEST_LIST = ("9352", "273952")

SERVER_TEST_LIST = ("9352", "273952", "144491")

TEST_LIST = SHORT_TEST_LIST

DOMAIN = "http://datacentral.aao.gov.au"

RESTFUL_BASE = "/asvo/sov/"

AUTH = ('sami', 'aat_hexa_61')

GZIP = ""

# LOCAL_DATA_PATH = "/Users/agreen/Documents/ASVO/test_data/sami_test_release/"
LOCAL_DATA_PATH = "/net/aaolxz/iscsi/data/SAMI/"

def download_fits_at_url(url, local_dir):
    """A helper function to download a FITS file from the given URL."""
    # urlretrieve(DOMAIN + RESTFUL_BASE + url, local_dir)


    full_url = DOMAIN + RESTFUL_BASE + url + "?format=fits"
    print(full_url)
    r = requests.get(full_url, stream=True, auth=AUTH)

    # Extract the filename the server suggests:
    filename = r.headers['content-disposition'].split("filename=")[1]

    with open(local_dir + filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_dir + filename


class TestSamiValueAddProvenance:


    @pytest.yield_fixture
    def tmpdir(self):

        with tempfile.TemporaryDirectory() as tempdir:
            yield tempdir

    def test_velocity_map_1_comp(self, tmpdir):


        local_filename_template = LOCAL_DATA_PATH + "data_products/EmissionLineFits/EmissionLineFitsV02/1_comp/{filename}.fits" + GZIP

        for object_id in TEST_LIST:
            url_template = "sami/{objid}/velocity_map-ionized_gas:1_comp/"
            remote_filename = download_fits_at_url(url_template.format(objid=object_id), tmpdir)

            local = fits.open(local_filename_template.format(filename=(object_id + "_1_comp")))
            remote = fits.open(remote_filename)

            assert local['V'].data[1, 25, 25] == remote[0].data[25, 25]

            assert_array_equal(local['V'].data[1], remote[0].data)


    def test_velocity_map_m_comp(self, tmpdir):
        local_filename_template = LOCAL_DATA_PATH + "data_products/EmissionLineFits/EmissionLineFitsV02/recom_comp/{filename}.fits" + GZIP

        for object_id in TEST_LIST:
            url_template = "sami/{objid}/velocity_map-ionized_gas:recom_comp/"
            remote_filename = download_fits_at_url(url_template.format(objid=object_id), tmpdir)

            local = fits.open(local_filename_template.format(filename=(object_id + "_recom_comp")))
            remote = fits.open(remote_filename)

            print(remote.info())

            assert local['V'].data[1, 25, 25] == remote['COMP1_V'].data[25, 25]

            assert_array_equal(local['V'].data[1], remote['COMP1_V'].data)

            assert_array_equal(local['V'].data[2], remote['COMP2_V'].data)
            assert_array_equal(local['V'].data[3], remote['COMP3_V'].data)

    def test_velocity_dispersion_map_m_comp(self, tmpdir):
        local_filename_template = LOCAL_DATA_PATH + "data_products/EmissionLineFits/EmissionLineFitsV02/recom_comp/{filename}.fits" + GZIP

        for object_id in TEST_LIST:
            url_template = "sami/{objid}/velocity_dispersion_map-ionized_gas:recom_comp/"
            remote_filename = download_fits_at_url(url_template.format(objid=object_id), tmpdir)

            local = fits.open(local_filename_template.format(filename=(object_id + "_recom_comp")))
            remote = fits.open(remote_filename)

            print(remote.info())

            assert local['VDISP'].data[1, 25, 25] == remote['COMP1_VDISP'].data[25, 25]

            assert_array_equal(local['VDISP'].data[1], remote['COMP1_VDISP'].data)

            assert_array_equal(local['VDISP'].data[2], remote['COMP2_VDISP'].data)
            assert_array_equal(local['VDISP'].data[3], remote['COMP3_VDISP'].data)