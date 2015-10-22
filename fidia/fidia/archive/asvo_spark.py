"""
A FIDIA archive plugin to support the initial efforts of the AAT ASVO Node.



"""

__author__ = "Andy Green"


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

        @TODO For now, this assumes that the first column contains the
        @identifier.

        """

        # Get Query Results from Spark (as a SchemaRDD object):
        results_rdd = hive_context.sql(query_string)

        # Convert to a Pandas DataFrame
        results_pddf = results_rdd.toPandas()

        # Set the key to be the first column
        results_pddf.set_index(results_pddf.columns[0], inplace=True)

        # Create an empty sample, and populate it via it's private interface
        # (no suitable public interface at this time.)
        new_sample = Sample()
        id_cross_match = pd.DataFrame(pd.Series(results_pddf.index, 
                    name='ASVO',
                    index=results_pddf.index))
        print(id_cross_match)
        new_sample.extend(id_cross_match)

        self.tabular_data = results_pddf

        new_sample._archives = {self}

        # Finally, we mark this new sample as immutable.
        new_sample.mutable = False

        return new_sample


