class DataSet(object):
	"""A FIDIA dataset"""
	def __init__(self):
		self.archives = set()
		self.contents = set()
		super(DataSet, self).__init__()

	def add_archive(self, archive):
		self.archives.add(archive)

		


