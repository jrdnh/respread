.. _getting_started:

***************
Getting started
***************

This guide introduces fundamental concepts with a simple operating statement example. The basic model structure consists of a top-level operating node which has revenue and expense child nodes. Each child node holds two additional line item functions.

::

    OperatingStatement (Node)
    ├── Revenue (Node)
    │   ├── product_revenue (func)
    │   └── service_revenue (func)
    └── OperatingExpenses (Node)
        ├── cogs (func)
        └── other_expenses (func)

The intial sections describe how to construct node-children trees. The later sections discuss additional considerations by extending the basic operating statement model.

.. toctree::
    :maxdepth: 1

    grouping_functions
    organizing_nodes
    navigating_nodes
    recursion_limits
    redirects

