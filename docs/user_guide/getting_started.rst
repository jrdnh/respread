.. _getting_started:

***************
Getting started
***************

This guide introduces fundamental concepts by creating model that builds simple loan schedules. The loans have annual interest payments until the maturity when the principal balance is repaid in full. The final model structure will have a top-level node that holds a sub-node with period start/end date leaf functions and additional leaf functions for loan balances and payments.

::

    Loan (Node)
    ├── Schedule (Node)
    │   ├── period_start (func)
    │   └── period_end (func)
    ├── beginning_balance (func)
    ├── interest_payment (func)
    ├── principal_payment (func)
    └── ending_balance (func)

.. toctree::
    :maxdepth: 2

    grouping_functions
    organizing_nodes
    navigating_nodes
    recursion_limits

