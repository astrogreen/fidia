.. toctree::
	:maxdepth: 2

	introduction
	tutorial
	api

What is FIDIA?
==============

FIDIA stands for "Format Independent Data Interface for Astronomy." In a
nutshell, it is a generic way to interact programatically in python with
astronomical data.

For the purposes of the AAT-ASVO node, FIDIA can be thought of as the
high-level data model. Through a plugin, it interfaces with the
low-level data model which is inside of Hadoop/Spark/Cassandra/etc.

Sample code:

.. code:: python

    >>> mysample = Sample.new_sample_from_archive('dynamo')
    >>> mysample.galaxies
    ['HfluxLz_15-3', 'MfluxLz_21-1']
    >>> mysample['HfluxLz_15-3']
    Galaxy "HfluxLz_15-3" at 15h34m13.4s -04d34m03.3s
    >>> mysample['HfluxLz_15-3'].redshift
    0.05432
    >>> mysample.add_archive_for_existing('SDSS')
    >>> mysample['HfluxLz_15-3'].image['SDSS-r']
    <<image>>
    >>> mysample['HfluxLz_15-3'].redshift
    WARNING: Multiple redshifts availabe, displaying from primary Archive "DYNAMO";
    0.05432
    >>> mysample['HfluxLz_15-3'].redshift.all
    ['dynamo': 0.05432, 'sdss': 0.054291]

Major Concepts
==============

Samples
-------

Samples have a concept of what objects they contain (may or may not be
all of the objects offered by a particular archive.)

Samples know which archives contain data for a given object, and what
kinds of data are offered:

For exmaple, a survey might mantain a dictionary of properties as keys
with values as the corresponding archive which contains their values.

Samples also allow for tabular access to the data. Data filtering is
achieved by creating new (sub) sample.

Archives
--------

Archives know how to load the data from disk or remote server (in a
possibly lazy way).

Archives return individual data objects in response to requests
forwarded by a Sample object.

Archives include machinery for local caching (in memory and on disk).

Astronomical Objects
--------------------

Astronomical Objects (Stars and Galaxies) define standard kinds of data
that can be retreived about them, etc. These are the objects that
Samples contain.

Samples may update these objects when a new archive is loaded, or they
may simply mark existing objects as invalid (@TODO!). Similarly, samples
may create all these objects as needed, or may wait until they are
explicitly requested.

Properties
----------

Properties are the quantities associated with astronomical objects. They
understand things like:

-  Units
-  Value
-  Error (possibly different in positive and negative direction)
-  Upper and lower limits where there is no detection/measurement
-  Description of what they are

.. code:: python

    >>> from fidia import Sample
    >>> from fidia.properties.photometry import *
    >>> mysample = Sample()

    # Assign a magnitude (via convenience function provided by AstroObject)
    >>> mysample['M31'].mag["SDSS r"] =  -19.4
    # This is the same as:
    >>> mysample['M31'].mag["SDSS r"].value = -19.4

    # Set the error on the measurement
    >>> mysample['M31'].mag["SDSS r"].error = 0.05

Use Cases and examples
======================

Starting something new:
-----------------------

.. code:: python

    >>> mysample = Sample()
    # Creates an in-memory archive, the default (?)
    >>> mysample.galaxies
    []
    >>> mysample['HfluxLz_15-3'].redshift = 0.523
    >>> mysample['HfluxLz_15-3'].redshift
    0.523
    >>> mysample['HfluxLz_15-3'].ra = 15*15.3
    >>> mysample['HfluxLz_15-3'].dec = -34.234
    >>> mysample['HfluxLz_15.3']
    Galaxy 'HfluxLz_15-3' at 15h20m -34d10m
    >>> mysample.add_archive_for_existing('SDSS')
    >>> mysample['HfluxLz_15-3'].image['SDSS-r']
    <<image>>
    >>> mysample['HfluxLz_15-3'].redshift
    WARNING: Multiple redshifts availabe, displaying from primary Archive "DYNAMO";
    0.05432
    >>> mysample['HfluxLz_15-3'].redshift.all
    ['inmemory': 0.05432, 'sdss': 0.054291]



