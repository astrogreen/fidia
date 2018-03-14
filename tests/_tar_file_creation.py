# Copyright (c) Australian Astronomical Observatory (AAO), 2018.
#
# The Format Independent Data Interface for Astronomy (FIDIA), including this
# file, is free software: you can redistribute it and/or modify it under the terms
# of the GNU Affero General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import pytest

# Standard Library Imports
import tempfile
import subprocess
import contextlib
import os

from astropy.io import fits

# FIDIA Imports
from fidia.archive.example_archive import ExampleArchive
# Other user imports
from fidia_tarfile_helper import fidia_tar_file_generator, Streaming


@contextlib.contextmanager
def working_directory(path):
    """A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.

    """
    prev_cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prev_cwd)

SAMPLE_NAME = "Example"

class TestTarFiles:


    @pytest.fixture
    def example_sample(self):
        return ExampleArchive().get_full_sample()

    @pytest.yield_fixture
    def example_tar_file(self, example_sample):
        with tempfile.TemporaryDirectory() as temp_directory:
            trait_path_list = [
                {'sample': SAMPLE_NAME,
                 'object_id': 'Gal1',
                 'trait_path': [
                     "image-red"
                 ]},
                {'sample': SAMPLE_NAME,
                 'object_id': 'Gal1',
                 'trait_path': [
                     "image-blue"
                 ]},
                {'sample': SAMPLE_NAME,
                 'object_id': 'Gal1',
                 'trait_path': [
                     "image-blue",
                     "image-red"
                 ]}
            ]

            stream = Streaming(fidia_tar_file_generator(example_sample, trait_path_list),
                               "example.tar.gz")
            stream.filename = temp_directory + "/example.tar.gz"
            stream.stream()

            yield stream.filename

    def test_tar_file_creation(self, example_tar_file):

        # Check exit codes for errors:
        assert subprocess.call(("tar", "-tzvf", example_tar_file)) == 0

    def test_tar_file_contents(self, example_tar_file):

        with tempfile.TemporaryDirectory() as untar_dir:
            # Untar the file into a new temporary directory.
            subprocess.call(("tar", "-C", untar_dir, "-xzvf", example_tar_file))

            print(subprocess.check_output(("ls", untar_dir)))

            # Check the contents of the directory:
            assert os.path.exists(os.path.join(untar_dir, SAMPLE_NAME))

            # Check that a few files exist based on the trait_path_list above:
            assert os.path.exists(os.path.join(untar_dir, SAMPLE_NAME, 'Gal1', 'image-red.fits'))
            assert os.path.exists(os.path.join(untar_dir, SAMPLE_NAME, 'Gal1', 'image-blue.fits'))
            assert os.path.exists(os.path.join(untar_dir, SAMPLE_NAME, 'Gal1', 'image-blue', 'image-red.fits'))

            # Check the FITS files are valid:
            fits.open(os.path.join(untar_dir, SAMPLE_NAME, 'Gal1', 'image-red.fits')).verify('exception')
            fits.open(os.path.join(untar_dir, SAMPLE_NAME, 'Gal1', 'image-blue', 'image-red.fits')).verify('exception')