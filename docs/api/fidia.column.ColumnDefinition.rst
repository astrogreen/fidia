ColumnDefinition
================

.. currentmodule:: fidia.column

.. autoclass:: ColumnDefinition
   :show-inheritance:

   .. rubric:: Attributes Summary

   .. autosummary::

      ~ColumnDefinition.column_type
      ~ColumnDefinition.id

   .. rubric:: Methods Summary

   .. autosummary::

      ~ColumnDefinition.associate
      ~ColumnDefinition.class_name
      ~ColumnDefinition.from_id
      ~ColumnDefinition.get_timestamp
      ~ColumnDefinition.on_associate

   .. rubric:: Attributes Documentation

   .. autoattribute:: column_type
   .. autoattribute:: id

   .. rubric:: Methods Documentation

   .. automethod:: associate
   .. automethod:: class_name
   .. automethod:: from_id
   .. automethod:: get_timestamp
   .. automethod:: on_associate

   .. rubric:: Abstract Methods for Original Data Retrieval

   .. method:: object_getter(object_id, **kwargs)

   Abstract method describing how to retrieve original data for one object in 
   this column.

   One of `.object_getter` or `.array_getter` must be defined by sub-classes
   in order for them to retrieve original data.

   Keyword arguments given by sub-classes implementing this abstract method
   are given special treatment as described at `.associate`. They refer to 
   attributes of the `.Archive` class to which this column belongs.

   .. method:: array_getter(**kwargs)

   Abstract method describing how to retrieve original data for every object 
   in this column.

   One of `.object_getter` or `.array_getter` must be defined by sub-classes
   in order for them to retrieve original data.

   Keyword arguments given by sub-classes implementing this abstract method
   are given special treatment as described at `.associate`. They refer to 
   attributes of the `.Archive` class to which this column belongs.


   .. rubric:: Abstract Properties and Methods for optimized data retrieval

   Data ingestion in the :doc:`Data Access Layer </fidia/api/dal>` can use
   these functions to optimise ingestion such that e.g. files or other
   expensive to set up resources that can be re-used are reused. See the
   optimizations in :meth:`fidia.dal.DataAccessLayer.ingest_archive` for more
   information.

   .. attribute:: grouping_context

   A string defining the unique grouping this column belongs to.

   This can be anything, but it should be sufficiently unique to avoid name
   clashes.

   Any column returning the same `grouping_context` will be assumed to be
   compatible with the context returned by `.prepare_context` below.

   .. method:: prepare_context

   Returns a context manager for retrieving data from any column sharing this column's `grouping_context`.

   The arguments are the same as those for `ColumnDefinition.object_getter`
   or `ColumnDefinition.array_getter` depending on which optimisation is
   relevant for this column.

   .. method:: object_getter_from_context(object_id, context, *args)

   Retrieve original data for this column using the provided open context.

   The arguments are the same as those for
   `ColumnDefinition.object_getter`, except for the addition of the open
   context in the second position.

   .. method:: array_getter_from_context(context, *args)

   Retrieve original data for this column using the provided open context.

   The arguments are the same as those for
   `ColumnDefinition.array_getter`, except for the addition of the open
   context in the first position.