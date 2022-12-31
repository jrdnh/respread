.. _seriesgroup:
===================
SeriesGroup classes
===================

.. currentmodule:: respread

Constructors
~~~~~~~~~~~~
.. autosummary::
   :toctree:

   SeriesGroup
   DynamicSeriesGroup

Hierarchy and navigation
~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
   :toctree:

   SeriesGroup.set_parent
   SeriesGroup.children
   SeriesGroup.add_child
   SeriesGroup.attr_above
   DynamicSeriesGroup.get_derived_children
   DynamicSeriesGroup.series_factory

Iteration
~~~~~~~~~
.. autosummary::
   :toctree:

   SeriesGroup.__iter__
   SeriesGroup.items
   SeriesGroup.names

Cache management
~~~~~~~~~~~~~~~~
.. autosummary::
   :toctree:

   SeriesGroup.cache_clear
