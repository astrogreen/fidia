

class FIDIAException(Exception):
    def __init__(self, *args):
        self.message = args[0]

class DataNotAvailable(FIDIAException): pass

class NotInSample(FIDIAException): pass

class UnknownTrait(FIDIAException): pass

class MultipleResults(FIDIAException): pass

class ReadOnly(FIDIAException): pass

class SchemaError(FIDIAException): pass

class ValidationError(FIDIAException): pass

class TraitValidationError(ValidationError): pass

class ArchiveValidationError(ValidationError): pass