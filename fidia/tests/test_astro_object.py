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

import pytest

from fidia import Sample, AstronomicalObject
from fidia.traits import Trait
from fidia.archive.example_archive import ExampleArchive

class TestAstronomicalObject:

    @pytest.fixture
    def example_archive_sample(self):
        ar = ExampleArchive()
        sample = ar.get_full_sample()
        return sample

    @pytest.fixture
    def example_object(self, example_archive_sample):
        obj = example_archive_sample['Gal1']
        return obj




