"""

The FIDIA Column System
-----------------------

Columns in FIDIA handle a single piece of data for all objects in an
:class:`.Archive` or :class:`.Sample`. Effectively, they can be thought of as a
single column of data from a catalog. The individual elements of the column must
be 'atomic' in the sense that they are a single number or single array of
numbers. (So a redshift and its error will be two separate columns, but an image
is a single column consisting of 2D arrays.)

The Columns system can be broken into two broad categories: classes that define
columns (based on :class:`.ColumnDefinition`) and classes that are the columns
of data themselves (based on :class:`.FIDIAColumn`).

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

from .columns import FIDIAColumn, FIDIAArrayColumn, ColumnID

from .column_definitions import *

__all__ = ['FIDIAColumn', 'FIDIAArrayColumn', 'ColumnID'] + column_definitions.__all__