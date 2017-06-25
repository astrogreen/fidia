from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict

from typing import List, Dict, Tuple, Iterable
import fidia

# Python Standard Library Imports
import os.path
import json
import re

# Other Library Imports
import pandas as pd
from astropy.io import fits
from astropy.io import ascii
import yaml



# FIDIA Imports
from fidia.column import *
from fidia.traits import *
# Other modules within this package

# Set up logging
import fidia.slogging as slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

# __all__ = ['Archive', 'KnownArchives', 'ArchiveDefinition']

def finder_fits_file(fits_path_pattern, object_id, basepath=''):

    columns_found = []
    fits_dict = OrderedDict()

    fits_mapping = []

    fits_path = os.path.join(basepath, fits_path_pattern.format(object_id=object_id))
    with fits.open(fits_path) as f:

        log.debug("Input FITS HDU Ordering: %s", [hdu.name for hdu in f])

        # Iterate over each Header Data Unit
        for hdu in f:

            if hdu.data is None:
                # Skip empty HDUs
                continue

            header_dict = OrderedDict()
            header_mappings = []

            for header in hdu.header:
                if header == "":
                    # Some FITS files can have empty strings or empty header keywords, which we cannot store.
                    continue

                # column_id = "FITSHeaderColumn:example_fits_file_path[{ext}].header[{keyword}]".format(
                #     ext=hdu.name,
                #     keyword=header)
                kw_type = type(hdu.header[header]).__name__
                kw_comment = hdu.header.cards[header].comment

                log.debug("Type of header KW '%s': %s", header, kw_type)
                log.debug("Comment of header KW '%s': %s", header, kw_comment)

                comment_match = re.match("(?:\[(?P<unit>[^\]]+)\] )?(?P<comment>.*)", kw_comment)
                if comment_match is not None:
                    unit = comment_match.group("unit")
                    kw_comment = comment_match.group("comment")
                else:
                    unit = ""

                column = FITSHeaderColumn(fits_path, hdu.name, header,
                                          type=kw_type, unit=unit, short_desc=kw_comment)

                column_id = column.id
                log.debug(repr(column))

                log.info("FOUND COLUMN_ID: %s", column_id)
                columns_found.append(column)
                header_dict[header] = column_id

                header_mappings.append(TraitPropertyMapping(header, column.id))

                # header_mappings.append(TraitPropertyMapping(header, column.id))



            column = FITSDataColumn(fits_path, hdu.name)
            hdu_dict = {"data": column.id, "header": header_dict}

            hdu_mapping = TraitMapping(FitsImageHdu, hdu.name, [
                TraitPropertyMapping("data", column.id),
                TraitMapping(FITSHeader, "header", header_mappings)
            ])


            fits_dict[hdu.name] = hdu_dict
            fits_mapping.append(hdu_mapping)

    # print(yaml.dump(fits_dict))
    # print(json.dumps(fits_dict, indent=2))
    # print(yaml.dump(columns_found))
    # print(json.dumps(columns_found, indent=2))

    return columns_found, fits_dict, fits_mapping

def finder_csv_file(file_pattern, comment="\s*#", index_column=None, basepath=""):

    columns_found = []

    table_dict = OrderedDict()
    table_mapping = []

    csv_path = os.path.join(basepath, file_pattern)
    table = ascii.read(csv_path, format="csv", comment=comment)

    import astropy.table.column

    for colname in table.colnames:
        # col = table.columns[colname]  # type: astropy.table.column.MaskedColumn

        column = CSVTableColumn(file_pattern, colname, index_column, comment)
        columns_found.append(column)

        table_dict[colname] = column.id
        table_mapping.append(TraitPropertyMapping(colname, column.id))


    return columns_found, table_dict, table_mapping
