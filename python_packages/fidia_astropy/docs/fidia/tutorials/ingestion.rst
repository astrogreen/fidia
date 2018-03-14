..  Copyright (c) Australian Astronomical Observatory (AAO), 2018.
 
    The Format Independent Data Interface for Astronomy (FIDIA), including this file, is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation,     either version 3 of the License, or (at your option) any later version.
    
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
    
    You should have received a copy of the GNU Affero General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.

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


