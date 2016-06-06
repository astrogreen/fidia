from __future__ import unicode_literals
import csv
from collections import defaultdict
from rest_framework.renderers import *
from six import StringIO, text_type
from rest_framework_csv.orderedrows import OrderedRows
from rest_framework_csv.misc import Echo

# six versions 1.3.0 and previous don't have PY2
try:
    from six import PY2
except ImportError:
    import sys    
    PY2 = sys.version_info[0] == 2


class FlatCSVRenderer(BaseRenderer):
    """
    Renderer which serializes to CSV
    """

    media_type = 'text/csv'
    format = 'csv'
    level_sep = '.'
    headers = None

    def render(self, data, media_type=None, renderer_context=None):
        """
        Renders serialized *data* into CSV. For a dictionary:
        """
        temp_head = ''
        temp_data = []
        # Serve only the queryResults field, strip all other meta data
        data_name = renderer_context['data_name']
        column_name = renderer_context['column_name']
        json_property_name = renderer_context['json_property_name']

        if json_property_name in data:
            if data_name in data[json_property_name]:
                temp_data = data[json_property_name][data_name]
            else:
                temp_data = []
            if column_name in data[json_property_name]:
                temp_head = data[json_property_name][column_name]
            else:
                temp_head = ''

        table = [temp_head] + temp_data

        # table looks as
        # [['cataid', 'z', 'metal'], [8823, 0.0499100015, 0.0163168724], [63147, 0.0499799997, 0.0380015143],
        #       [91963, 0.0499899983, 0.0106879927]]
        # where the column headers are the first row.

        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        for row in table:
            # Assume that strings should be encoded as UTF-8
            csv_writer.writerow([
                elem.encode('utf-8') if isinstance(elem, text_type) and PY2 else elem
                for elem in row
            ])

        return csv_buffer.getvalue()
