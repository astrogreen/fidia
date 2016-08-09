from . import Trait


# Logging Import and setup
from .. import slogging
log = slogging.getLogger(__name__)
log.setLevel(slogging.DEBUG)
log.enable_console_logging()


class MetadataTrait(Trait):
    def __init__(self, *args, **kwargs):
        super(MetadataTrait, self).__init__(*args, **kwargs)




class DetectorCharacteristics(MetadataTrait):
    """

    Trait Properties:

        detector_id

        detector_size

        gain

        read_noise


    """

    required_trait_properties = {
        'detector_id': 'string',
        'detector_size': 'string',
        'gain': 'float',
        'read_noise': 'float'
    }

class SpectrographCharacteristics(Trait):
    """

    Trait Properties:

        instrument_name

        arm

        disperser_id

        disperser_configuration

        control_software

    """

    pass

class OpticalTelescopeCharacteristics(Trait):
    """

    Trait Properties:

        observatory_name

        latitude

        longitude

        altitude

        focus_configuration



    """
    pass


