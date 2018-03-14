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

class ExportException(ValidationError): pass

class TraitValidationError(ValidationError): pass

class ArchiveValidationError(ValidationError): pass