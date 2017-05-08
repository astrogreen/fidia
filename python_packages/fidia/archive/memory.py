#!/usr/bin/env python
"""An in-memory FIDIA archive format, primarily for testing."""

from fidia.base_classes import BaseArchive
from ..astro_object import AstronomicalObject

class MemoryArchive(BaseArchive):

    def __init__(self):
        super(MemoryArchive, self).__init__()

        self.contents = dict()

    def writeable(self):
        return True

    @property
    def default_object(self):
        return AstronomicalObject

    def add_object(self, value):
        self.contents[value.identifier] = value