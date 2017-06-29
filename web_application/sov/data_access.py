import fidia, os, sys
import base64
from io import BytesIO
from PIL import Image
from collections import OrderedDict
from sov.helpers.dummy_data.astro_object import ARCHIVE
from sov.helpers.dummy_data.survey import SURVEYS


def get_archive():
    return ARCHIVE


def get_dummy_image():
    """
    Dummy image from file
    Returns: base64 encoded string

    """
    dir = os.path.dirname(__file__)
    filepath = os.path.join(dir, 'dummy_data/G09_Y1_FS2_052.png')
    im = Image.open(filepath)

    # convert png to jpeg, saving in memory
    rgb_im = im.convert(mode='RGBA')
    buffer = BytesIO()
    rgb_im.save(buffer, format="JPEG")

    img_str = base64.b64encode(buffer.getvalue())

    return {
        "src": img_str,
        "meta": {
            "encoding": "base64", "format": "jpg", "size": rgb_im.size, "mode": rgb_im.mode,
            "caption": "GAMA Spectrum SPECID = G09_Y1_FS2_052"
        }
    }


def get_data_for_trait(archive=None, trait_key=None, astro_object=None):
    """
    return data for trait
    Args:
        astro_object:
        archive
        trait_key
    Returns:
        Data
    """

    trait = {}
    if trait_key == '1_table_trait2':
        trait = {
            "data": [
                ['prop1', 1, 2, 3, 4, 5, 6], ['prop2', 4, 5, 3, 4, 5, 6], ['prop3', 7, 8, 3, 4, 5, 6]
            ],
            "header": [
                {"name": 'col1', "type": 'int', 'text': '-'},
                {"name": 'col2', "type": 'int', 'text': 'value'},
                {"name": 'col3', "type": 'int', 'text': 'unit'},
                {"name": 'col6', "type": 'int', 'text': 'header'},
                {"name": 'col7', "type": 'int', 'text': 'header2'},
                {"name": 'col8', "type": 'int', 'text': 'header3'},
                {"name": 'col9', "type": 'int', 'text': 'header4'}
            ],
            "type": "table"
        }
    if trait_key == '1_image_trait1':
        trait = get_dummy_image()
        trait["type"] = "image"
    return trait
