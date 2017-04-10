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

from .columns import FIDIAColumn, FIDIAArrayColumn

from .column_definitions import ColumnDefinition, ColumnDefinitionList, \
    FITSHeaderColumn, FITSDataColumn