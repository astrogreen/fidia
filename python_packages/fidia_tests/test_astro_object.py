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




