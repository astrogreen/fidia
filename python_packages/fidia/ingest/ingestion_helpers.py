from __future__ import absolute_import, division, print_function, unicode_literals

# from typing import Union, Tuple, Dict, Type
# import fidia

# Python Standard Library Imports
import json

# Other Library Imports

# FIDIA Imports

# Set up logging
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()



def collect_validation_errors(output, breadcrumb=tuple()):
    result = []
    if isinstance(output, dict):
        for key, value in output.items():
            if key == 'validation_errors':
                result.append(("At " + " -> ".join(breadcrumb), value))
                # Don't process this key further:
                continue
            if isinstance(value, (dict, list)):
                result.extend(collect_validation_errors(value, breadcrumb=breadcrumb + (str(key),)))
    if isinstance(output, list):
        for key, value in enumerate(output):
            if isinstance(value, (dict, list)):
                result.extend(collect_validation_errors(value, breadcrumb=breadcrumb + ("(Item:" + str(key) + ")",)))
    return result

def format_validation_errors(errors):
    output_lines = []
    for item in errors:
        output_lines.append(item[0])
        for elem in item[1]:
            output_lines.append(4*" " + elem)
    return "\n".join(output_lines)


def write_validataion_errors(specification_dict, errors_filename):
    with open(errors_filename, "w") as f:
        f.write(format_validation_errors(collect_validation_errors(specification_dict)))

def write_specification_dict_as_json(specification_dict, json_filename):
    with open(json_filename, "w") as f:
        json.dump(specification_dict, f, indent=4)

def update_mappings_list_with_specification_dict(mappings, columns, updated_specification_dict):
    # type: (List[TraitMapping], Dict[str, dict]) -> List
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