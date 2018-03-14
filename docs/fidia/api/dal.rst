..  Copyright (c) Australian Astronomical Observatory (AAO), 2018.
 
    The Format Independent Data Interface for Astronomy (FIDIA), including this file, is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation,     either version 3 of the License, or (at your option) any later version.
    
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
    
    You should have received a copy of the GNU Affero General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.

=================
Data Access Layer
=================


Design
======

The DAL must be persisted in a way that is specific to a particular environment in which FIDIA is running. Remember, the golden goal is to be able to write a FIDIA-based algorithm in Python on a laptop, run it against locally available data, and then upload the code to the Data Central server (or some other FIDIA-based archive), and have it run without modification. Of course, the assumption here is that the data used is available on both machines under the same Archive.

To achieve this environment independence, there must be an environment independent way to access data from an archive. The first step to make this possible has already been done: hijack the creation of :class:`~fidia.Archive` instances. Let’s consider someone creates an archive in order to access data::

	from fidia.archives import ExampleArchive

	ar = ExampleArchive(basepath="/path/to/data")

Here :class:`~fidia.archive.example_archive.ExampleArchive` is actually an :class:`~fidia.archive.ArchiveDefinition` object. That archive definition (possibly) contains a finalised version of the “ingest” code: i.e. a list of Column(Definitions) and a collection of Mappings. However, when one requests a instance of `ExampleArchive` as above, one is actually calling an `Archive` factory, which is defined in in `ArchiveDefinition.__new__()`.  This factory checks the MappingDB to see if the requested archive has previously been created (even in another session of Python/FIDIA), and, if so, simply restores that `Archive` object from the database. If not then the factory constructs a new `Archive` and returns it.

An `ArchiveDefinition` can decide to some extent when an Archive should be a separate instance by determining how the (unique) `archive_id` attribute is defined. If the `ArchiveDefinition` returns an `archive_id` that matches an existing Archive in the database, then it will be loaded. In the case of the `ExampleArchive` above, the `archive_id` is always `’ExampleArchive'` regardless of where the base path of the initialisation. So I can write code on my computer that tells FIDIA to load the ExampleArchive from a particular location on disk. But on the Data Central server, the location could be different (or even non-existant, as I’ll explain in a moment) and yet it would still know that we are talking about the same thing. However, an `ArchiveDefinition` could also be explicit about some things, too: consider::

	SAMIArchive(basepath="/tmp/ingest/sami", release="DR1")

The `SAMIArchive` (definition) could include the `release` value in the `archive_id`,  and then multiple distinct  `Archives` could exist.

So, I’m imaging the DAL both leveraging this portability and being implemented using a generally similar approach. In my mind, layers of the DAL used by a particular FIDIA instance would be defined in the `fidia.ini` file.  They would be defined in a series of sections, one per DAL layer, each one having a marker to show it was a section describing a DAL layer. For example::

	[MappingDatabase]
	engine = sqlite
	location = 
	database = :memory:
	echo = True
	[DAL-PrestoDB]
	url = "presto://127.0.0.1/presto"
	parameter1 = value
	parameter2 = another_value
	[DAL-AdcPermissions]
	ad_server = 127.0.0.1:8080

When fidia starts up, it would do something like the following to initialize its internal Data Access Layer:

1. Create an empty list containing all layers of the DAL.
2. Read through the config, finding all DAL sections.
3. Iterate through the DAL sections. for each, it would:

	1. Create an instance of the corresponding class, calling the constructor with all of the items of that configuration section, e.g.:
	`fidia.dal.PrestoDB(url="presto://127.0.0.1/presto”, paramter1=“value”, parameter2=“another_value”)`
	2. Add that instance to the list of DALs.

Once this list was initialised, instances of :class:`~fidia.FIDIAColumn` would be able to call into the list whenever they are asked for data. These calls would contain enough information to enable any layer of the DAL to find and return the data if it has it available. Each layer would basically have three options for handling a request: return the data, pass the request on to the next layer,  or raise an exception. Exceptions raised would explain the problem (DataNotAvailabe, or maybe PermissionDenied). 

There will need to be a way of aggregating requests for data. I’ll admit that I haven’t thought much about this, other than to get so far as working out that the obvious place to decide what should be aggregated is either on the Trait (e.g. gather all data for columns referenced by this Trait), or by some kind of column grouping (when data for a column is requested, get data for any other column which belongs to the same ColumnGroup).

The nature of how the request for data is passed around or what the request contains is not yet clear to me. Probably, it will need to be it’s own data structure/Python object.




Reference/API
=============

.. automodapi:: fidia.dal

.. automodapi:: fidia.dal._dal_internals
