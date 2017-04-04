from __future__ import absolute_import, division, print_function, unicode_literals

class BaseArchive(object):

    def writeable(self):
        raise NotImplementedError("")

    # @property
    # def contents(self):
    #     raise NotImplementedError("")

    def get_full_sample(self):
        raise NotImplementedError("")

    def get_trait(self, object_id=None, trait_key=None, parent_trait=None):
        raise NotImplementedError("")
