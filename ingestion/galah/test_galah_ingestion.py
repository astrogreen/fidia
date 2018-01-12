import pytest

from galah_fidia_ingestion import *

import astropy
import astropy.coordinates

import fidia

@pytest.fixture(scope="module")
def galah_archive():
    ar = GALAH_iDR2(basepath=GALAH_DATA_DIR)
    return ar

def test_galah_archive_creation(galah_archive):
    assert isinstance(galah_archive, fidia.Archive)

def test_all_columns_mapped(galah_archive):
    # type: (fidia.Archive) -> None

    unmapped_columns = galah_archive._validate_all_columns_mapped()

    if unmapped_columns:
        print("Unmapped columns found:")
        for c in unmapped_columns:
            print("   ", c)
        assert False, "test_all_columns_mapped found %s unmapped columns" % len(unmapped_columns)

def test_no_missing_columns(galah_archive):
    # type: (fidia.Archive) -> None

    missing_columns = galah_archive._validate_mapping_column_ids()

    if missing_columns:
        print("Missing columns found:")
        for c in missing_columns:
            print("   ", c)
        assert False, "test_no_missing_columns found %s missing columns" % len(missing_columns)

def test_coordinates(galah_archive):
    # type: (fidia.Archive) -> None

    a_gid = next(iter(galah_archive.contents))

    assert galah_archive[a_gid].sky_coordinate["galah"].get_unit('ra') == "degree"

    coord = galah_archive[a_gid].sky_coordinate["galah"].coord

    assert isinstance(coord, astropy.coordinates.SkyCoord)

