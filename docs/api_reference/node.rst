.. _node:

============
Node classes
============

.. currentmodule:: respread

Constructors
~~~~~~~~~~~~
.. autosummary::
   :toctree:

   Node
   DynamicNode

Hierarchy and navigation
~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
   :toctree:

   Node.set_parent
   Node.children
   Node.add_child
   Node.attr_above
   DynamicNode.get_derived_children
   DynamicNode.child_factory

Iteration
~~~~~~~~~
.. autosummary::
   :toctree:

   Node.__iter__
   Node.items
   Node.names

Cache management
~~~~~~~~~~~~~~~~
.. autosummary::
   :toctree:

   Node.cache_clear
