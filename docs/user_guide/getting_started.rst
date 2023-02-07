.. _getting_started:

***************
Getting started
***************

This guide introduces fundamental concepts by building a simple loan schedule. The loan has annual interest-only payments until the loan principal is fully repaid at maturity. The final project structure will have a top-level node that holds a i) sub-node with period start/end date leaf functions and ii) leaf functions for loan economics.

::

    Loan (Node)
    ├── Schedule (Node)
    │   ├── period_start (func)
    │   └── period_end (func)
    ├── beginning_balance (func)
    ├── interest_payment (func)
    ├── principal_payment (func)
    └── ending_balance (func)

================================
Grouping functions with ``Node``
================================

``respread`` organizes functions into callable, composite nodes. A ``Node`` class (or subclass) holds a tuple of attribute names indicating which attributes are children. Adding a child is as simple as adding its attribute name to ``children``.

.. code-block:: python

    >>> from datetime import date
    >>> from dateutil.relativedelta import relativedelta

    >>> from respread import Node

    >>> def period_start(period):
    ...     return date(2020, 1, 1) + relativedelta(years=1) * period

    >>> schedule = Node()
    >>> # equivalent to schedule.period_start = period_start; schedule.children = ('period_start',)
    >>> schedule.add_child('period_start', period_start)

.. code-block:: python

    >>> schedule.children
    ('period_start',)

    >>> schedule.period_start(0)
    datetime.date(2020, 1, 1)

Binding functions to a ``Node`` object allows the function to access the object's other attributes, including other children.

.. note:: "Binding" a function to an object implicitly passes that object as the first argument. Functions defined in a class are automatically bound when they are accessed by instances of that class. The first argument is referred to as ``self`` by convention.

        Use ``MethodType`` to manually bind a function. Generally, as shown later in this guide, you will not need to manually bind functions.

.. code-block:: python

    >>> from types import MethodType

    >>> def period_end(self, period):
    ...     # `self` will refer to the 'schedule' object after it is bound
    ...     # The end date is the start date for the next period
    ...     return self.period_start(period + 1)

    >>> schedule.add_child('period_end', MethodType(period_end, schedule))

.. code-block:: python

    >>> schedule.children
    ('period_start', 'period_end')

    >>> [schedule.period_end(p) for p in range(3)]
    [datetime.date(2021, 1, 1), datetime.date(2022, 1, 1), datetime.date(2023,1, 1)]


===========================
Organizing Nodes into trees
===========================

``Node`` objects are callable themselves. When a ``Node`` object is called, it will propogate the call down to its children with the same function arguments. The return value will be a tuple containing the responses of each child. The order of responses is determined by the order in the ``children`` property.

.. code-block:: python

    >>> schedule(0)
    (datetime.date(2020, 1, 1), datetime.date(2021, 1, 1))

Since ``Node`` objects are callable, they can be nested as children to create tree hierarchies. ``Node`` objects have a special ``parent`` attribute that is used to point to a node's parent node. The ``set_parent`` method is a convenience tool that sets the parent and returns the object for a more fluent workflow.

.. code-block:: python

    >>> loan = Node()
    >>> loan.add_child('schedule', schedule.set_parent(loan))

.. code-block:: python

    >>> loan.children
    ('schedule',)

    >>> schedule.parent is loan
    True

Calling the top-level node calls each childr node in turn. Ultimately, it returns a flat tuple of the leaf function results.

.. code-block:: python

    >>> loan.add_child('index_rate', lambda period: 0.05)

.. code-block:: python

    >>> loan.children
    ('schedule', 'index_rate')

    >>> loan(0)
    (datetime.date(2020, 1, 1), datetime.date(2021, 1, 1), 0.05)

``Node`` objects have several additional methods to inspect the function hierarchy by name, provide named responses, and iterate through children.

.. code-block:: python

    >>> loan.names()  # child names, concatenated by a period (default)
    ('schedule.period_start', 'schedule.period_end', 'index_rate')

    >>> loan.items(period=0)  # ((child, names), child_result)
    ((('schedule', 'period_start'), datetime.date(2020, 1, 1)), (('schedule', 'period_end'), datetime.date(2021, 1, 1)), (('index_rate',), 0.05))

    >>> loan.display(period=0)  # (names, child_results) tuples where errors are ignored
    (('schedule.period_start', datetime.date(2020, 1, 1)), ('schedule.period_end', datetime.date(2021, 1, 1)), ('index_rate', 0.05))

    >>> loan_iterator = iter(loan)  # iterate over ((child, names), child_function)
    >>> next(loan_iterator)
    (('schedule', 'period_start'), <function period_start at 0x109c53370>)
    >>> next(loan_iterator)
    (('schedule', 'period_end'), <bound method period_end of <respread.node.Node object at 0x109c55300>>)
    >>> next(loan_iterator)
    (('index_rate',), <function <lambda> at 0x109d30b80>)

=================
Managing children
=================

``Node`` objects recognize any attribute that has the property ``is_component == True`` as a child. ``Node`` objects have ``is_component`` property enabled by default. 

Objects recognized as children during regular attribute assignment will be automatically added as children.

.. code-block:: python

    >>> def credit_spread(period):
    ...     return 0.02

    >>> credit_spread.is_component = True
    >>> loan.credit_spread = credit_spread
    >>> loan.children
    ('schedule', 'interest_rate', 'credit_spread')

Rather than defining functions and nodes separately, you can use the ``child`` decorator to add the ``is_component`` property to functions defined in ``Node`` subclass defitions. Those functions will be added as children during initialization.

Let's redefine the schedule and loan types with a few modifications and add payment terms.

.. code-block:: python

    >>> from respread import child

    >>> class Schedule(Node):
    ...     def __init__(self, start_date: date, period_lenth: relativedelta):
    ...         super().__init__()
    ...         self.start_date = start_date
    ...         self.period_length = period_lenth
    ...     @child
    ...     def period_start(self, period):
    ...         return self.start_date + self.period_length * period
    ...     @child
    ...     def period_end(self, period):
    ...         return self.period_start(period + 1)

    >>> class Loan(Node):
    ...     def __init__(self, coupon, amount, tenor, schedule: Schedule):
    ...         super().__init__()
    ...         self.add_child('schedule', schedule, index=0)
    ...         self.coupon = coupon
    ...         self.amount = amount
    ...         self.tenor = tenor
    ...     @child
    ...     def beginning_balance(self, period):
    ...         return self.amount if period == 0 else self.ending_balance(period - 1)
    ...     @child
    ...     def interest_payment(self, period):  # uses actual / 360 caclulation convention
    ...         yf = (self.schedule.period_end(period) - self.schedule.period_start(period)).days / 360
    ...         return self.coupon * yf * self.beginning_balance(period)
    ...     @child
    ...     def principal_payment(self, period):
    ...         return self.beginning_balance(period) if period == (self.tenor - 1) else 0
    ...     @child
    ...     def ending_balance(self, period):
    ...         return self.beginning_balance(period) - self.principal_payment(period)

You can then create a loan schedule as follows. This loan object assumes a 10-year term starting 2020-01-01 at 7.0% with a principal amount of 100.

.. code-block:: python

    >>> import pandas as pd

    >>> loan = Loan(coupon=0.07,
    ...             amount=100,
    ...             tenor=10,
    ...             schedule=Schedule(start_date=date(2020, 1, 1),
    ...                               period_lenth=relativedelta(years=1)))

.. code-block:: python

    >>> loan.names()
    ('schedule.period_start', 'schedule.period_end', 'beginning_balance', 'interest_payment', 'principal_payment', 'ending_balance')

    >>> yrs = range(loan.tenor)
    >>> pd.DataFrame([loan(y) for y in yrs], columns=loan.names(), index=yrs)
    schedule.period_start schedule.period_end  beginning_balance  interest_payment  principal_payment  ending_balance
    0            2020-01-01          2021-01-01                100          7.116667                  0             100
    1            2021-01-01          2022-01-01                100          7.097222                  0             100
    2            2022-01-01          2023-01-01                100          7.097222                  0             100
    3            2023-01-01          2024-01-01                100          7.097222                  0             100
    4            2024-01-01          2025-01-01                100          7.116667                  0             100
    5            2025-01-01          2026-01-01                100          7.097222                  0             100
    6            2026-01-01          2027-01-01                100          7.097222                  0             100
    7            2027-01-01          2028-01-01                100          7.097222                  0             100
    8            2028-01-01          2029-01-01                100          7.116667                  0             100
    9            2029-01-01          2030-01-01                100          7.097222                100               0

Notice that the only magic numbers hardcoded into the class definitions are in the interest calculation convention (actual / 360). With a few minor adjstments, the ``Loan`` class could be updated to take different calculation conventions, amortization schedules, holiday adjustments, or any other term that might change. Additionally, you could create a test suite to help ensure validity of edge cases (e.g. negative period inputs).

The flexibilty of components built with ``respread`` drives modeling efficiency since components can be easily reused and configured.

============================
Recursion limits and caching
============================

Assume we had with *daily* interest periods for a five year term instead of *annual* interest periods from previous example. We could model it using the same class definitions as follows.

.. code-block:: python

    >>> start_date = date(2020, 1, 1)
    >>> end_date = date(2025, 1, 1)
    >>> periods = (end_date - start_date).days

    >>> daily_loan = Loan(coupon=0.07,
    ...                   amount=100,
    ...                   tenor=periods,
    ...                   schedule=Schedule(start_date=start_date,
    ...                                     period_lenth=relativedelta(days=1)))


However, there is a problem when calling the final loan period.

.. code-block:: python

    >>> daily_loan(daily_loan.tenor - 1)
    <Traceback>
    RecursionError: maximum recursion depth exceeded

The ``Schedule.period_start`` function is directly recursive. The ``beginning_balance`` and ``ending_balance`` functions in ``Loan`` are also indirectly recusive since they rely on each other back to the zeroth period. 

By default, Python limits the callstack to a depth of 1,000 frames. However, there are 1,827 daily periods in the schedule. Since a new frame is added for each recursive call, calling the 1,827th period reaches the maximum call depth before reaching the zeroth period and resolving.

.. note:: Different environments have different recursion limits. For example, IPython/Jupyter generally has a limit of 3,000.

        You can check the max depth by running ``import sys; sys.getrecursionlimit()``.

        It is possible, although not recommended, to change the limit with ``sys.setrecursionlimit(new_limit)``.

Recursion is a natural, concise way to define many operations. ``respread`` addresses depth limits with caching and iteration.

The ``cached_child`` decorator is similar to the ``child`` decorator except it wraps functions in a per-Node-instance cache.

The snippet below redefines ``Schedule`` and ``Loan`` with caching decorators for the recursive functions.

.. code-block:: python
    :emphasize-lines: 8, 11, 22, 32

    >>> from respread import cached_child

    >>> class Schedule(Node):
    ...     def __init__(self, start_date: date, period_lenth: relativedelta):
    ...         super().__init__()
    ...         self.start_date = start_date
    ...         self.period_length = period_lenth
    ...     @cached_child
    ...     def period_start(self, period):
    ...         return self.start_date + self.period_length * period
    ...     @cached_child
    ...     def period_end(self, period):
    ...         return self.period_start(period + 1)

    >>> class Loan(Node):
    ...     def __init__(self, coupon, amount, tenor, schedule: Schedule):
    ...         super().__init__()
    ...         self.add_child('schedule', schedule, index=0)
    ...         self.coupon = coupon
    ...         self.amount = amount
    ...         self.tenor = tenor
    ...     @cached_child
    ...     def beginning_balance(self, period):
    ...         return self.amount if period == 0 else self.ending_balance(period - 1)
    ...     @child
    ...     def interest_payment(self, period):  # actual / 360 convention
    ...         yf = (self.schedule.period_end(period) - self.schedule.period_start(period)).days / 360
    ...         return self.coupon * yf * self.beginning_balance(period)
    ...     @child
    ...     def principal_payment(self, period):
    ...         return self.beginning_balance(period) if period == (self.tenor - 1) else 0
    ...     @cached_child
    ...     def ending_balance(self, period):
    ...         return self.beginning_balance(period) - self.principal_payment(period)

The functions in our classes are not pure functions. They depend on object state (coupon rate, amount, tenor, etc.). 

``cached_child`` functions will usually depend on some object state. Whenever using a cached wrapper, calls should be placed in a context manager. Placing a ``Node`` in a context manager clears caches across the entire tree on entry and on exit. 

Now that the recursive functions are cached, we can iterively call from the zeroth period to any arbitrarily large period in the future. 

.. code-block:: python

    >>> start_date = date(2020, 1, 1)
    >>> end_date = date(2025, 1, 1)
    >>> periods = (end_date - start_date).days
    >>> daily_loan = Loan(coupon=0.07,
    ...                   amount=100,
    ...                   tenor=periods,
    ...                   schedule=Schedule(start_date=start_date,
    ...                                     period_lenth=relativedelta(days=1)))

.. code-block:: python

    >>> with daily_loan as dl:
    ...     for p in range(periods):
    ...         payoff_period = dl(p)

    >>> print(payoff_period)
    (datetime.date(2024, 12, 31), datetime.date(2025, 1, 1), 100, 0.019444444444444445, 100, 0)

This is the end of the **Getting started** guide!

Start using ``respread``, dive deeper into the documentation, or visit the project site to `ask questions <https://github.com/jrdnh/respread/issues>`_ or `contribute <https://github.com/jrdnh/respread>`_!
