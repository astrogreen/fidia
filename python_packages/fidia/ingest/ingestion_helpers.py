"""
FIDIA Ingestion Helpers Overview
--------------------------------

This module contains a few convenience functions for handling FIDIA structuring
information.

"""
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

from __future__ import absolute_import, division, print_function, unicode_literals

from typing import List, Dict, Tuple, Union
import fidia

# Python Standard Library Imports
import json

# Other Library Imports

# FIDIA Imports

# Set up logging
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()

__all__ = ['collect_validation_errors', 'format_validation_errors', 'write_validataion_errors',
           'write_specification_dict_as_json',
           'update_mappings_list_with_specification_dict']

def collect_validation_errors(specification_dict, breadcrumb=tuple()):
    # type: (Union[Dict, List], Tuple) -> List[Tuple[str, str]]
    """Extract all validation errors found in the specification dictionary.

    When a structuring is converted to a dictionary using
    :meth:`TraitMapping.as_specification_dict`, that function includes a list of
    validation errors at each level of the structuring under the key
    "validation_errors". This function finds and extracts all of those errors by
    recursing through the specification_dict.

    Parameters
    ----------
    specification_dict: dictionary or list
        The specification structure to search.
    breadcrumb: tuple (used internally)
        The starting location in the structure (used internally for recursion).

    Returns
    -------
    list
        A list of Tuples containing the string describing the location as the
        first element, and the string describing the error as the second
        element.

    """

    result = []  # type: List[Tuple[str, str]]
    if isinstance(specification_dict, dict):
        for key, value in specification_dict.items():
            if key == 'validation_errors':
                result.append(("At " + " -> ".join(breadcrumb), value))
                # Don't recurse on this key, so skip to the next iteration of the for loop.
                continue
            if isinstance(value, (dict, list)):
                # Recurse to sub-dicts of this key.
                result.extend(collect_validation_errors(value, breadcrumb=breadcrumb + (str(key),)))
    if isinstance(specification_dict, list):
        # @TODO: Not sure that lists are still required? Original S7 format vs updated format?
        for key, value in enumerate(specification_dict):
            if isinstance(value, (dict, list)):
                # Recurse to sub-dicts of this list_item.
                result.extend(collect_validation_errors(value, breadcrumb=breadcrumb + ("(Item:" + str(key) + ")",)))
    return result


def format_validation_errors(errors):
    """Format validation errors for display.

    Converts the output of `.collect_validation_errors` into a single string for
    printing/writing to file.

    """
    output_lines = []
    for item in errors:
        output_lines.append(item[0])
        for elem in item[1]:
            output_lines.append(4*" " + elem)
    return "\n".join(output_lines)


def write_validataion_errors(specification_dict, errors_filename):
    """Collect all validation errors in specification_dict and write to errors_filename."""
    with open(errors_filename, "w") as f:
        f.write(format_validation_errors(collect_validation_errors(specification_dict)))


def write_specification_dict_as_json(specification_dict, json_filename):
    """Write out specification_dict to json_filename in JSON format."""
    with open(json_filename, "w") as f:
        json.dump(specification_dict, f, indent=4)


def update_mappings_list_with_specification_dict(mappings, columns, updated_specification_dict):
    # type: (List[fidia.traits.TraitMapping], Dict[str, dict]) -> List
    """Update a list of TraitMapping objects using the serialised mapping information in updated_specification_dict.

    This identifies the part of the specification_dict that corresponds to each
    TraitMapping object in the list, and then calls the
    `update_with_specification_dict` method.

    """

    update_log = []

    for mapping in mappings:
        log.debug("Preparing to update %s", mapping.mapping_key_str)
        if mapping.mapping_key_str in updated_specification_dict:
            # The mapping appears in the updated information, so update mapping with that representation
            log.debug("Updated mapping information found, updating mapping...")
            log_length_before = len(update_log)
            mapping.update_with_specification_dict(updated_specification_dict[mapping.mapping_key_str],
                                                   columns=columns, update_log=update_log)
            log_length_after = len(update_log)
            if log_length_after > log_length_before:
                log.debug("%s updates made", log_length_after - log_length_before)
                if log.isEnabledFor(slogging.VDEBUG):
                    for line in update_log[log_length_before:]:
                        log.vdebug(line)
            else:
                log.debug("No updates required.")
        else:
            # The mapping does not appear in the updated information: perhaps it has been deleted?
            log.debug("No updated mapping information found! Perhaps item has been deleted from JSON? No changes made.")

    return update_log
