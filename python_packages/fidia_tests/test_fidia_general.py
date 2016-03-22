"""
These tests check that the modules import, and that the namespace is populated
as expected.

"""
import logging

class FidiaGeneralTest:

	def check_sample_imports(self):
		from fidia import Sample

	# def test_logging_debug_turned_off(self):
	# 	import fidia
     #    import fidia.archive
     #    import fidia.sample
     #    import fidia.traits.base_traits
     #    import fidia.traits.utilities
     #    import fidia.traits.galaxy_traits
     #    import fidia.traits.generic_traits
     #    import fidia.traits.stellar_traits
    #
     #    log = logging.getLogger('fidia')
     #    for child_logger in log.
