import tarfile
from io import BytesIO

import os.path

import logging
logging.basicConfig(format='%(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

import fidia
import fidia.traits as traits


def format_trait_path_as_path(trait_key, include_branch_version=False):
    # type: (Union[TraitKey, str], bool) -> str
    """Reformat a TraitKey for use in file-system paths."""

    tk = traits.TraitKey.as_traitkey(trait_key)
    return tk.trait_name

def filename_for_trait_path(trait_path):
    """Produce a filename for a trait_path, including a path section to deal with hierarchical data.

    We create a hierarchy suitable for storage in a TAR archive. The levels are as follows:

    - The sample name as the top level directory (not an absolute path)
    - The object_id as a directory

    The next two levels are only included if necessary to get to the actual Trait to be saved.

    - The Trait Key as a directory. Branch and version information is always included, but separated with "-"
    - Sub Trait names, recursing through all sub_traits but the last.

    Finally, the filename is defined:

    - Object id, then trait key, with the branch and version included if top level trait, but separated with "-"

    """

    # The sample name as the top directory
    path = trait_path['sample']

    # Append the object_id as the next level
    path = os.path.join(path, trait_path['object_id'])

    # Work through any levels of sub-traits:
    remaining_path_elements = len(trait_path['trait_path'])
    for elem in trait_path['trait_path']:
        if remaining_path_elements == 1:
            # Have reached the final element of the trait_path, which will make the filename.
            filename_element = elem
            break
        else:
            # Have not yet reached the final element of the path, so interviening
            # elements should be added as sub-directories
            formatted_path = format_trait_path_as_path(elem)
            path = os.path.join(path, elem)
            remaining_path_elements -= 1

    # Finally, get the filename
    filename = format_trait_path_as_path(filename_element)
    filename += ".fits"
    path = os.path.join(path, filename)

    return path

def fits_file_generator(sample, trait_path_list):
    """A generator which creates FITS files from FIDIA Objects in the
    provided Trait list and corresponding TarInfo objects.

    """

    assert isinstance(sample, fidia.Sample)

    for trait_path in trait_path_list:

        astro_object = sample[trait_path['object_id']]

        # Drill down the trait_path
        trait = astro_object
        for elem in trait_path['trait_path']:
            trait = trait[elem]

        fits_file = BytesIO()

        trait.as_fits(fits_file)

        # Seek the fits_file buffer back to the start, so that it can be read in
        # again. (Or should this be done by using the "getbuffer" method?)
        fits_file.seek(0)

        # Create the file name for this FITS file within the TAR file.
        filename = filename_for_trait_path(trait_path)

        ti = tarfile.TarInfo(filename)
        ti.size = len(fits_file.getbuffer())

        log.debug("Size of file '%s' to be added to tar: '%s'" % (filename, ti.size))
        yield (ti, fits_file)

def streaming_targz_generator(tar_info_generator, stream_buffer):
    """Generator which takes the output of a tar_info_generator and writes it as a Tar File to the stream_buffer"""

    assert isinstance(stream_buffer, StreamBuffer)

    tar_file = tarfile.open('download.tar.gz', mode='w|gz', fileobj=stream_buffer)

    for tar_info, fileobj in tar_info_generator:

        tar_file.addfile(tar_info, fileobj)

        yield stream_buffer.retrieve_and_clear()

    tar_file.close()
    # Flush remaining bytes stored to the file in the close step
    yield stream_buffer.retrieve_and_clear()

def fidia_tar_file_generator(sample, trait_path_list):
    # type: (fidia.Sample, List) -> Streaming
    """Something like a Django view that streams a tar file."""

    assert isinstance(sample, fidia.Sample)

    stream_buffer = StreamBuffer()

    fits_generator = fits_file_generator(sample, trait_path_list)
    tar_generator = streaming_targz_generator(fits_generator, stream_buffer)

    response = Streaming(tar_generator, "example.tar.gz")
    return response



class StreamBuffer(object):
    """A simple file-like object which acts as a streaming buffer.

    This implements only the `write` and `tell` functions of the file-like
    interface. Then it implements an additional methods for getting data within
    the buffer.

    """
    def __init__(self):
        self._offset = 0
        self._storage = b""
        # Initially no data.
        self._contents_retrieved = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def tell(self):
        """Provide the current offset in the "file".

        This is just how many bytes have been written to the StreamBuffer in total.

        """
        return self._offset

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""

        # There is nothing to do unless we have actually been given data.
        if len(value) > 0:
            if self._contents_retrieved:
                log.warning("Buffer contents have been retrieved but not cleared, and new data is being added.")
                self._contents_retrieved = False

            self._storage += value
            self._offset += len(value)
            if log.isEnabledFor(logging.DEBUG):
                # log.debug("New Bytes Received: '%s'", value)
                log.debug("Total bytes received: %s" % self._offset)
        else:
            log.debug("Write called with no data.")

    def retrieve(self):
        """Retrieve the outstanding contents of the buffer (i.e. that which has not been handled)"""
        if len(self._storage) > 0:
            self._contents_retrieved = True
        return self._storage

    def clear(self):
        """Clear outstanding contents of the buffer"""

        # There is nothing to do unless there is actually outstanding data.
        if len(self._storage) > 0:
            if self._contents_retrieved:
                self._storage = b""
                self._contents_retrieved = False
            else:
                raise BufferError("Attempt to clear StreamBuffer without retrieving contents first.")

    def retrieve_and_clear(self):
        result = self.retrieve()
        self.clear()
        return result

    def close(self):
        if self._contents_retrieved or len(self._storage) == 0:
            # Okay to close. Delete remaining contents
            self.clear()
        else:
            raise BufferError("Attempt to close StreamBuffer which still contains data.")

class Streaming:
    """A Test Class similar to Django's StreammingHttpResponse."""
    def __init__(self, iter, filename):
        self.iter = iter
        self.filename = filename
        self._file_open = False
        self._total_bytes_written = 0

    def open_file(self):
        if not self._file_open:
            self.file = open(self.filename, 'wb')
            self._file_open = True

    def stream(self):
        if not self._file_open:
            self.open_file()
        for i in self.iter:
            # print("Streaming: ", i)
            self.file.write(i)
            self._total_bytes_written += len(i)
            if len(i) > 0:
                print("Bytes Written: %s, Total Bytes Written: %s" % (len(i), self._total_bytes_written))

