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
