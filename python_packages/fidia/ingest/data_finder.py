from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Iterable
import fidia

# Python Standard Library Imports
import os.path
import json
import re

# Other Library Imports
import pandas as pd
from astropy.io import fits
import yaml



# FIDIA Imports
from fidia.column import FITSHeaderColumn, FITSDataColumn
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
    fits_mapping = dict()

    fits_path = os.path.join(basepath, fits_path_pattern.format(object_id=object_id))
    with fits.open(fits_path) as f:
        # Iterate over each Header Data Unit
        for hdu in f:

            header_mapping = dict()

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
                header_mapping[header] = column_id

            column = FITSDataColumn(fits_path, hdu.name)
            hdu_mapping = {"data": column.id, "header":header_mapping}

            fits_mapping[hdu.name] = hdu_mapping

    # print(yaml.dump(fits_mapping))
    # print(json.dumps(fits_mapping, indent=2))
    # print(yaml.dump(columns_found))
    # print(json.dumps(columns_found, indent=2))

    return columns_found, fits_mapping