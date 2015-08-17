from fidia.archive import MemoryArchive, BaseArchive

class TestArchive:
	def test_create_inmemory_archive(self):
		m = MemoryArchive()
		assert isinstance(m, BaseArchive)