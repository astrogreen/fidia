=====================
Introduction to FIDIA
=====================



What is FIDIA?
==============

FIDIA stands for "Format Independent Data Interface for Astronomy." Broadly,
it is intended to provide a system for accessing astronomical data that
requires no understanding of how the data is stored. There are two major
layers of the abstraction. The first is a standardisation of data access
regardless of the original data format, and (to a lesser extent) the location
of the data (on disk, in the cloud, etc.). The second is a standard approach
for structuring that data. Ultimately, FIDIA provides a generic way to
interact programatically in python with astronomical data.


Sample code:

.. code:: python

    >>> example_archive = ExampleArchive(basepath=test_data_dir)
    >>> example_archive.contents
    ["Gal1", "Gal2", "Gal3"]
    >>> example_archive['Gal1']
    Galaxy "HfluxLz_15-3" at 15h34m13.4s -04d34m03.3s
    >>> mass = example_archive['Gal1'].dmu['StellarMasses'].table['StellarMasses'].stellar_mass



Data management and structuring
===============================

Data made available through FIDIA is represented internally as an unstructured
series of columns containing the actual data and a structured hierarchy that locates the columns.

Columns
-------

A column in FIDIA is a set of individual pieces of data. The cells of this
column each contain a single piece of data, and the data type of all cells is
consistent for the whole column. The single piece of data could be something
like a float, a double, a (variable length) string, etc., or it could be an
array of those items with arbitrary dimensions. An example of an array would
be the floating point numbers making up an image or spectrum (the former being
2D and the latter 1D). In addition to the the data, FIDIA columns also have
metadata about the data in the column, such as unit, a short description, etc.

Archives
--------

An archive defines a set of objects and a corresponding set of columns of data
about those objects. Typically, the objects referred to in an archive will all
be of the same kind: stars, galaxies, observatories, observations, etc. 

Structuring information: Mappings
---------------------------------

FIDIA organises the atomic data stored in Columns into a hierarchical
structure using Mappings. Effectively, a set of mappings defines which columns
data will appear at a particular leaf on the hierarchical data tree. Data from
a particular column can appear as multiple distinct leaves on the tree, so the
mappings can define several distinct schemas for the data that are overlaid
on top of one another.


Samples
-------

A Sample is the result of running any kind of query or selection of all
available data. Like archives, Samples typically contain objects of only one
type (e.g. just stars or just galaxies). Samples do not contain any data, but
instead maintain pointers to the original Archives from which they were
selected, and therefore expose all of the data available in those archives.



Connecting data to the system
=============================

FIDIA only can know about data that it has been told about. Adding a new data
set to FIDIA is referred to as "ingestion" and the code or steps that execute
that ingestion are a "plugin".

The plugin consists of two parts: a definition of the columns of data
available, and a structuring of those columns. The definitions of the columns
tell FIDIA how to find data, whether by loading it from disk, querying a
database, or requesting it over the internet. Although it is possible to load
data from almost anywhere, FIDIA includes a set of predefined column
definitions to handle standard cases like loading data from a FITS file or its
header. The second part of the plugin defines an initial structuring of the
data. Here is where the data is organised together in a meaningful way. Again,
any organisation is possible, but FIDIA comes with some standard structures.
Using these standard structures as much as possible makes your data available
in a way that other users will expect and understand.

Depending on how you use FIDIA, data may be "ingested" every time you start up
FIDIA/Python, or it may be cached so that it is already available any time you
use FIDIA in Python.



Working with data in FIDIA
==========================

Once data has been ingested into FIDIA, it can be accessed by requesting the Archive containing it:

.. code:: python
	
	import fidia
	example_archive = fidia.known_archives.by_id["ExampleArchive"]
	...





