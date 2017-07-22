"""
Archives in FIDIA
=================

An archive in FIDIA represents a collection of data for a particular set of
objects. An archive is defined by three things: a list of objects (stars,
galaxies, etc.), a list of columns of atomic data for those objects (e.g. a list
of masses or spectra), and a collection of TraitMappings (the hierarchical
structuring of the data in those columns).


Archives vs ArchiveDefinitions
------------------------------

`.ArchiveDefinitions` define what belongs in an archive and how to access/ingest
it. When their constructor is called, they act as factories for actual
`.Archive` objects, which are what one works with to actually access and process
data within FIDIA. A user wishing to bring new data into FIDIA will want to
subclass `.ArchiveDefinition` to define the data and objects of the archive to
be created.

When the constructor for an `.ArchiveDefinition` is called, it operates as a
factory for `.Archive` objects. Before creating a new object, the list of all
previously known archives is checked for an archive with the same ID as the
archive to be constructed. If the archive already exists, then it is loaded from
the MappingDB rather than being constructed afresh. This design allows FIDIA in
different environments (e.g. astronomer's laptop, data-centre server) to run the
same FIDIA code without modification even though the requested data may be
stored in very different places or methods.



How big is an archive/when are things different archives?
---------------------------------------------------------

Typically, a set of objects and data belong to the same archive when for most of
the objects in the archive, most of the kinds of data are also available. It is
often useful to think of how the data is indexed: a bunch of data indexed by a
Galaxy ID typically belongs together in an Archive, while data indexed by
Cluster ID would belong in a different archive (even if it comes from the same
survey).

"""

# __all__ = ['archive.Archive']

# from .base_archive import BaseArchive
# from .memory import MemoryArchive
#

# import fidia.archive.archive

from fidia.archive.archive import Archive, BasePathArchive, DatabaseArchive, ArchiveDefinition

# from fidia.archive.archive import *