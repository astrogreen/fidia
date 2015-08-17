

class BaseArchive(object):
    def __init__(self):
        super(BaseArchive, self).__init__()

    def writeable(self):
        raise NotImplementedError("")

    def contents(self):
        return list()
