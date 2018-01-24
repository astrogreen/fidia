"""
FIDIA Data Finders Overview
---------------------------

This module provides helpers for automatically finding available data in a
variety of standard file types/formats. These helpers are designed to explore an
example file or table provided, and then return both a list of the columns of
data available and also a structuring that represents how the data is organised
in the original format. The former provides a quick way to discover the data
available, and the latter provides a way that the original data could be
reconstructed by exporting the structuring provided. There is no requirement to use
the structuring information provided by these functions.

It is expected that the available helpers will continue to grew as new data
formats become popular.



"""

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Optional
# import fidia

# Python Standard Library Imports
import os.path
import re

# Other Library Imports
from astropy.io import fits
from astropy.io import ascii



# FIDIA Imports
from fidia.column import *
from fidia.traits import *
# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.WARNING)
log.enable_console_logging()

__all__ = ['finder_fits_file', 'finder_csv_file']

def finder_fits_file(fits_path_pattern, object_id, basepath=''):
    # type: (str, str, Optional[str]) ->  (List[FIDIAColumn], List[TraitMapping])
    """Find data columns and structuring for FITS files organised per object.

    Opens and explores the FITS file at the specified path for the given
    object ID as an example of what the corresponding FITS file would contain
    for any valid object id. Specifically it searches for:

    * the data part of Primary and Image extensions
    * The value of header keywords in any extension with data
        * The comment field for the header keyword will be used as the "short
          description" of the new column
        * If the comment field matches the pattern "[(unit)] Comment string",
          the "(unit)" will be used as the unit of the new column, otherwise
          the unit will be `None`.
        * The column type will be set to the Python type of the keyword value.

    Note that if an extension has no data (`hdu.data == None`), then the entire
    extension will be skipped.


    Parameters
    ----------
    fits_path_pattern: str
        The path pattern that will be used to find the FITS files in general.
        See XXX for a detailed description of the file_path_pattern expansion.
    object_id: str
        A valid object ID. This object ID will be used to find the example
        FITS file used to find data and define structure. Only the file for
        this single ID will be explored, so it should be representative.
    basepath: str
        The basepath of the archive that this data will belong to. See
        :class:`fidia.BasePathArchive` for more information.

    Returns
    -------
    columns_found: list of ColumnDefinitions
        All of the columns of data found.


    Notes
    -----
    Units with the name "Angstroem" are rewritten to "Angstrom" before they are
    stored. This would be much better handled elsewhere.

    """

    columns_found = []  # type: List[ColumnDefinition]
    fits_mapping = []  # type: List[TraitMapping]

    fits_path = os.path.join(basepath, fits_path_pattern.format(object_id=object_id))
    with fits.open(fits_path) as f:

        log.debug("Input FITS HDU Ordering: %s", [hdu.name for hdu in f])

        # Iterate over each Header Data Unit
        for hdu in f:

            if hdu.data is None:
                # Skip empty HDUs
                continue
                # Note: this may not always be the right thing to do. Worth
                # checking when this actually occurs and revisiting. For
                # example, there may be valid header keyword items in the
                # PrimaryHDU which would be skipped if the file only has valid
                # data in extensions.

            header_mappings = []

            for header in hdu.header:
                if header == "":
                    # Some FITS files can have empty strings or empty header keywords, which we cannot store.
                    continue

                kw_type = type(hdu.header[header]).__name__
                kw_comment = hdu.header.cards[header].comment

                log.debug("Type of header KW '%s': %s", header, kw_type)
                log.debug("Comment of header KW '%s': %s", header, kw_comment)

                comment_match = re.match("(?:\[(?P<unit>[^\]]+)\] )?(?P<comment>.*)", kw_comment)
                if comment_match is not None:
                    unit = comment_match.group("unit")
                    if unit == "Angstroem":
                        unit = "Angstrom"
                        # @TODO: This (fix for astropy shortcomings) should be done somewhere else!
                    kw_comment = comment_match.group("comment")
                else:
                    unit = None
                    # None is used for units that are "missing", typically in situations where no unit applies.

                column = FITSHeaderColumn(fits_path_pattern, hdu.name, header,
                                          dtype=kw_type, unit=unit, short_desc=kw_comment,
                                          n_dim=0)
                log.info("Found column_id: %s", column.id)
                columns_found.append(column)

                header_mappings.append(TraitPropertyMapping(header, column.id))

            data_shape = hdu.data.shape

            column = FITSDataColumn(fits_path_pattern, hdu.name,
                                    dtype=hdu.data.dtype.name, n_dim=len(data_shape))
            log.info("Found column_id: %s", column.id)
            columns_found.append(column)

            hdu_mapping = TraitMapping(FitsImageHdu, hdu.name, [
                TraitPropertyMapping("data", column.id),
                TraitMapping(FITSHeader, "header", header_mappings)
            ])

            fits_mapping.append(hdu_mapping)

    return columns_found, fits_mapping

def finder_csv_file(file_pattern, comment="\s*#", index_column=None, basepath=""):
    # type: (str, str, Optional[str], str) ->  (List[FIDIAColumn], List[TraitMapping])
    """Find data columns and structuring in a CSV file covering all objects.

    Opens and explores the CSV file at the specified path. The CSV file is
    indexed by the index_column. A column will be created for each column in the
    input CSV file, including any column defined as the index_column.


    Parameters
    ----------
    file_pattern: str
        The path to the CSV file.
    comment: str
        A string defining how a line in the CSV shall be identified as a
        comment. See :class:`CSVTableColumn` for more info.
    index_column: str
        The name of the column that will be used to index the table. This column
        should be populated with object_id's that make up the contents of the
        :class:`.Archive`.
    basepath: str
        The basepath of the archive that this data will belong to. See
        :class:`fidia.BasePathArchive` for more information.

    Returns
    -------
    columns_found: list of ColumnDefinitions
        All of the columns of data found.
    table_mapping: list of TraitMappings
        The structuring of the data in the table.

    """

    columns_found = []  # type: List[ColumnDefinition]
    table_mapping = []  # type: List[TraitMapping]

    csv_path = os.path.join(basepath, file_pattern)
    table = ascii.read(csv_path, format="csv", comment=comment)

    for colname in table.colnames:

        column = CSVTableColumn(file_pattern, colname, index_column, comment)
        columns_found.append(column)

        table_mapping.append(TraitPropertyMapping(colname, column.id))

    return columns_found, table_mapping
