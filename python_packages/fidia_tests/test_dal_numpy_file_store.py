# noinspection PyUnresolvedReferences
import pytest

import os
import tempfile
import subprocess
import warnings

import numpy as np
# from astropy.io import fits

import fidia
from fidia.archive.example_archive import ExampleArchive
from fidia.dal import NumpyFileStore

# noinspection PyUnresolvedReferences
import generate_test_data as testdata


@pytest.yield_fixture(scope='module')
def dal_data_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        yield tempdir


def test_ingestion_array_column(test_data_dir, dal_data_dir):
    ar = ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive

    # dal_data_dir = "/Users/agreen/scratch/dal/"

    array_column = ar.columns["ExampleArchive:FITSDataColumn:{object_id}/{object_id}_red_image.fits[0]:1"]

    file_store = NumpyFileStore(dal_data_dir)

    file_store.ingest_column(array_column)

    dir_text = subprocess.check_output(["ls", "-R", dal_data_dir])
    print(dir_text.decode())

    data_dir = os.path.join(
        dal_data_dir,
        "ExampleArchive",
        "FITSDataColumn",
        "{object_id}/{object_id}_red_image.fits[0]",
        "1",
    )

    # Check that the files are created
    for object_id in ar.contents:
        assert os.path.exists(os.path.join(data_dir, object_id + ".npy"))

    # Check that the dal can retrieve the data again, and it matches:
    for object_id in ar.contents:
        print(object_id)
        d = file_store.get_value(array_column, object_id)
        print(type(d))
        print(d.dtype)

        orig = ar[object_id].image["red"].data

        print(type(orig))
        print(orig.dtype)
        assert np.allclose(d, orig)
        assert np.array_equal(d, orig)

    # assert False


def test_ingestion_nonarray_column(test_data_dir, dal_data_dir):
    ar = ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive

    # dal_data_dir = "/Users/agreen/scratch/dal/"

    array_column = ar.columns["ExampleArchive:FITSBinaryTableColumn:stellar_masses.fits[1].data[ID->StellarMass]:1"]

    file_store = NumpyFileStore(dal_data_dir)

    file_store.ingest_column(array_column)

    dir_text = subprocess.check_output(["ls", "-R", dal_data_dir])
    print(dir_text.decode())

    data_dir = os.path.join(
        dal_data_dir,
        "ExampleArchive",
        "FITSBinaryTableColumn",
        "stellar_masses.fits[1].data[ID->StellarMass]",
        "1",
    )

    # Check that the files are created
    for object_id in ar.contents:
        assert os.path.exists(os.path.join(data_dir, "pandas_series.pkl"))

    # Check that the dal can retrieve the data again, and it matches:
    for object_id in ar.contents:
        d = file_store.get_value(array_column, object_id)
        assert np.array_equal(d, ar[object_id].dmu["StellarMasses"].table["StellarMasses"].stellar_mass)


def test_full_ingestion_removes_need_for_original_data(clean_persistence_database):
    """This test checks both the full ingestion, and that such an ingestion removes the need for the original data."""

    # NOTE: This works on a completely empty persistence database provided by the
    # `clean_persistence_database` fixture.


    with tempfile.TemporaryDirectory() as dal_data_dir:
        with tempfile.TemporaryDirectory() as test_data_dir:
            testdata.generate_simple_dataset(test_data_dir, 5)

            ar = ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive

            file_store = NumpyFileStore(dal_data_dir)
            file_store.ingest_archive(ar)

            # Add this layer to FIDIA's known data access layers
            fidia.dal_host.layers.append(file_store)

            dir_text = subprocess.check_output(["ls", "-R", dal_data_dir])
            print(dir_text.decode())

        assert not os.path.exists(test_data_dir)

        # Now check that data can still be accessed even after original data is removed.
        for object_id in ar.contents:
            ar[object_id].dmu["StellarMasses"].table["StellarMasses"].stellar_mass

        for object_id in ar.contents:
            ar[object_id].image["red"].data

        # Remove layer from FIDIA DAL to avoid problems with other tests:
        idx = fidia.dal_host.layers.index(file_store)
        del fidia.dal_host.layers[idx]

def test_types_are_preserved(test_data_dir, dal_data_dir):

    ar = ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive

    column = ar.columns["ExampleArchive:FITSHeaderColumn:{object_id}/{object_id}_red_image.fits[0].header[NAXIS]:1"]

    input_type = type(column.get_value("Gal1", provenance="definition"))

    assert input_type is int

    file_store = NumpyFileStore(dal_data_dir)
    file_store.ingest_column(column)

    output_type = file_store.get_value(column, "Gal1").dtype

    assert output_type == input_type


def test_ingestion_benchmarks(benchmark, clean_persistence_database, test_data_dir):

    with tempfile.TemporaryDirectory() as test_data_dir:
        testdata.generate_simple_dataset(test_data_dir, 30)

        ar = ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive

        def func():
            with tempfile.TemporaryDirectory() as dal_data_dir:

                file_store = NumpyFileStore(dal_data_dir)
                file_store.ingest_archive(ar)

                # Add this layer to FIDIA's known data access layers
                fidia.dal_host.layers.append(file_store)

                # Remove layer from FIDIA DAL to avoid problems with other tests:
                idx = fidia.dal_host.layers.index(file_store)
                del fidia.dal_host.layers[idx]

        benchmark(func)

def test_data_volumne(test_data_dir):

    def get_size(start_path='.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    ar = ExampleArchive(basepath=test_data_dir)  # type: fidia.Archive

    with tempfile.TemporaryDirectory() as dal_data_dir:
        file_store = NumpyFileStore(dal_data_dir)
        file_store.ingest_archive(ar)

        ingest_size = get_size(dal_data_dir)

    original_size = get_size(test_data_dir)

    # warnings.warn(UserWarning("NumpyFileStore disk usage = %s" % (ingest_size)))
    # warnings.warn(UserWarning("NumpyFileStore disk usage ratio original:ingest = %s" % (original_size/ingest_size)))


