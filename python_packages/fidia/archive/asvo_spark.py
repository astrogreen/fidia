"""
A FIDIA archive plugin to support the initial efforts of the AAT ASVO Node.



"""

__author__ = "Andy Green"

import time
import logging
log = logging.getLogger(__name__)

# External package imports
import pandas as pd

# Custom Packages
from fidia.asvo_spark import hive_context

# Relative imports in this package
from .base_archive import BaseArchive
from ..sample import Sample

class AsvoSparkArchive(BaseArchive):

    def __init__(self):
        super(AsvoSparkArchive, self).__init__()

        # Store connection to spark.
        self._hive_context = hive_context

        self.contents = dict()



    def writeable(self):
        return False

    @property
    def default_object(self):
        return None

    @property
    def name(self):
        return 'ASVO'
    

    def add_object(self, value):
        pass

    def new_sample_from_query(self, query_string):
        """Create a new FIDIA sample containing the query results.

        @TODO For now, an arbitrary index identifier is assigned.

        @TODO: Once the identifier has been sorted out, the code in
        `aatnode/views.py:QueryForm.post()` will need to be reviewed.

        """

        log.debug("Starting elapsed timer for function")
        start_time = time.clock()

        # Get Query Results from Spark (as a SchemaRDD object):
        results_rdd = hive_context.sql(query_string)

        log.debug("Elapsed time: %f", time.clock() - start_time)

        # Convert to a Pandas DataFrame
        results_pddf = results_rdd.toPandas()

        log.debug("Elapsed time: %f", time.clock() - start_time)

        # Set the key to be the first column
        #results_pddf.set_index(results_pddf.columns[0], inplace=True)


        log.debug("Elapsed time: %f", time.clock() - start_time)

        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        new_sample = Sample()
        id_cross_match = pd.Series(results_pddf.index,
                    name='ASVO',
                    index=results_pddf.index))
        log.debug("Elapsed time: %f", time.time() - start_time)
        # print(id_cross_match)
        new_sample.extend(id_cross_match)
        log.debug("Elapsed time: %f", time.time() - start_time)

        self.tabular_data = results_pddf

        new_sample._archives = {self}

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        log.debug("Elapsed time: %f", time.clock() - start_time)
        return new_sample


    def results_from_query(self, query_string):
        """
        This simply deals with results as it is. No indexing, cross-matching etc.
        :param query_string:
        :return:
        """

        # Get Query Results from Spark (as a SchemaRDD object):
        results_rdd = hive_context.sql(query_string)

        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        new_sample = Sample()

        self.tabular_data = results_rdd

        new_sample._archives = self

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        return new_sample