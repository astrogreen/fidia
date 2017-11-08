=========================
Ingesting data into FIDIA
=========================


This tutorial goes through two examples, one for a data set stored in FITS files, and one stored in a MySQL database. The underlying datasets used are the S7 and GAMA Surveys, respectively.

Ingesting a data set stored in FITS files: The S7 Survey
========================================================


Organization of the data
------------------------

S7 data consists of FITS and CSV files arranged into a loose directory structure.

* Spectral cubes (red and blue): stored as FITS files
* Spectral cubes with the broad component subtracted (red and blue): stored as
  FITS files, and **not present for all galaxies**.
* LZIFU Fits: stored using the standard LZIFU format, though not all lines are
  fit, so some FITS extensions are empty.
* LZIFU "best" components as determined by `LZcomp`: Similar format to LZIFU
  fits above.
* Nuclear spectra of all galaxies (red and blue): stored as FITS files.
* Broad component subtracted nuclear spectra of all galaxies (red and blue):
  stored as FITS files.
* Tabular data:
    * Catalog (CSV)
    * Nuclear fluxes (CSV)
    * Nuclear flux errors (CSV)
    * Nuclear luminosities (CSV)





Ingesting a data set stored in a MySQL database: The GAMA Survey
================================================================


