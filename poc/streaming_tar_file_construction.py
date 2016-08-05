import tarfile
from io import BytesIO

import logging


# from fidia.archive.example_archive import ExampleArchive

# sample = ExampleArchive().get_full_sample()
#
# def create_tar_from_fidia(download_list, fileobj):
#
#     tar_file = tarfile.TarFile("download.tar", mode='w', fileobj=fileobj)
#
#     for download in download_list:
#         object_id = download['object_id']
#         trait_path = download['trait_path']
#
#
#         # Drill down the trait_path:
#         current_trait = sample[object_id]
#         for trait_key in trait_path:
#             current_trait = current_trait[trait_key]
#
#         # Create buffer to store this trait in:
#         buf = BytesIO()
#
#         current_trait.as_fits(buf)
#
#         tar_info = tarfile.TarInfo.frombuf(buf)
#
#         tar_info.name = "/".join(trait_path)
#
#         tar_file.addfile(tar_info)
#
#         yield
#


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """
    def __init__(self):
        self._offset = 0
        self._storage = b""

    def tell(self):
        return self._offset

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""

        self._storage += value
        self._offset += len(value)
        if len(value) > 0:
            print(value)
            print("Total bytes received: %s" % self._offset)

class Streaming:
    def __init__(self, iter):
        self.iter = iter
        self.file = open("tmp.tar.gz", 'wb')
        self._total_bytes_written = 0

    def stream(self):
        for i in self.iter:
            # print("Streaming: ", i)
            self.file.write(i)
            self._total_bytes_written += len(i)
            if len(i) > 0:
                print("Bytes Written: %s, Total Bytes Written: %s" % (len(i), self._total_bytes_written))

# def some_streaming_csv_view():
#     """A view that streams a large CSV file."""
#     # Generate a sequence of rows. The range is based on the maximum number of
#     # rows that can be handled by a single sheet in most spreadsheet
#     # applications.
#     rows = (["Row {}".format(idx), str(idx)] for idx in range(65536))
#     pseudo_buffer = Echo()
#     writer = csv.writer(pseudo_buffer)
#
#     def stream_generator(rows):
#         for row in rows:
#             result = writer.writerow(row)
#             yield result
#
#     response = Streaming(stream_generator(rows))
#     return response

def some_streaming_tar_view():
    """A view that streams a large CSV file."""
    # Row = individual file
    # Writer = overall Tar file.

    pseudo_buffer = Echo()
    tar_file = tarfile.open('download.tar.gz', mode='w|gz', fileobj=pseudo_buffer)

    def tarinfo_generator():
        for idx in range(500):
            fileobj = BytesIO(bytes("Row {}".format(idx), 'utf-8'))
            ti = tarfile.TarInfo("{}.txt".format(idx))
            ti.size = len(fileobj.getbuffer())
            # print("Size of file to be added to tar: '%s'" % ti.size)
            yield (ti, fileobj)

    def stream_generator(rows):
        for row in rows:
            result = tar_file.addfile(*row)
            yield pseudo_buffer._storage
            pseudo_buffer._storage = b""
        tar_file.close()
        # Flush remaining bytes stored to the file in the close step
        yield pseudo_buffer._storage
    response = Streaming(stream_generator(tarinfo_generator()))
    return response

if __name__ == '__main__':
    stream = some_streaming_tar_view()

    stream.stream()

