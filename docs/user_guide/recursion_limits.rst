.. _recursion_limits:

****************************
Recursion limits and caching
****************************

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

    >>> with daily_loan as dl:
    ...     for p in range(periods):
    ...         payoff_period = dl(p)

    >>> print(payoff_period)
    (datetime.date(2024, 12, 31), datetime.date(2025, 1, 1), 100, 0.019444444444444445, 100, 0)

This is the end of the **Getting started** guide!

Start using ``respread``, dive deeper into the documentation, or visit the project site to `ask questions <https://github.com/jrdnh/respread/issues>`_ or `contribute <https://github.com/jrdnh/respread>`_!
