.. _recursion_limits:

****************************
Recursion limits and caching
****************************

The ``Revenue.product_revenue`` function was defined previously as shown below.

.. code-block:: python

    ... class Revenue(Node):
    ...     @child
    ...     def product_revenue(self, year: int) -> float:
    ...         return 100 * 1.08 ** (year - 2020)

This formula has a nice, closed form implementation. Often their aren't such tidy solutions, and it's easier to describe a series of numbers recursively.

The class definition below models product revenue on a *daily* basis as a function of the day of the week. Revenue starts at an annual rate of 100 . It doesn't grow at all on weekdays, but it grows 0.01% per day on the weekends.

.. code-block:: python

    >>> from datetime import date
    >>> from dateutil.relativedelta import relativedelta

    >>> class DailyRevenue(Node):
    ...     @child
    ...     def product_revenue(self, dt: date) -> float:
    ...         if dt == date(2020, 1, 1):
    ...             return 100 / 365
    ...         if dt.weekday() < 5:  # weekdays
    ...             return self.product_revenue(dt - relativedelta(days=1))
    ...         # weekends
    ...         return self.product_revenue(dt - relativedelta(days=1)) * 1.0001
    ...     ...

    >>> revenue = DailyRevenue()
    >>> initial_date = date(2020, 1, 1)
    >>> [revenue.product_revenue(initial_date + relativedelta(days=day)) for day in range(5)]
    [0.273972602739726, 0.273972602739726, 0.273972602739726, 0.27399999999999997, 0.2740274]

Although this example is contrived, but it highlights how complex interactions can be easier to model recursively.

However, there's a problem when trying to run long-dated projections. Trying to calculate revenue five years into the future results in a recursion limit error.

.. code-block:: python

    >>> revenue.product_revenue(date(2025, 1, 1))
    RecursionError: maximum recursion depth exceeded while calling a Python object

Python generally limits the call stack to 1,000 frames.

.. note::

    The exact limit depends on the environment. For example, IPython/Jupyter environments generally have a limit of 3,000 frames.

    You can check the max depth by running ``import sys; sys.getrecursionlimit()``.

    It is possible, although not recommended, to change the limit with ``sys.setrecursionlimit(new_limit)``.

``respread`` addresses depth limits with caching and iteration.

The ``cached_child`` decorator is similar to the ``child`` decorator except it wraps functions in a per-Node-instance cache. This means that caches are destroyed when node objects are destroyed.

The snippet below redefines the ``Revenue`` class with a caching decorator. The redefined class also parameterizes the initial date, value, and growth rate. Making the class configurable promotes reuse and makes it easier to modify at runtime.

.. code-block:: python
    :emphasize-lines: 13

    >>> from respread import cached_child

    >>> class DailyRevenue(Node):
    ...     def __init__(self, 
    ...                  initial_date: date, 
    ...                  initial_value: float,
    ...                  rate: float) -> None:
    ...         super().__init__()
    ...         self.initial_date = initial_date
    ...         self.initial_value = initial_value
    ...         self.rate = rate
    ...     
    ...     @cached_child
    ...     def product_revenue(self, dt: date) -> float:
    ...         if dt == self.initial_date:
    ...             return self.initial_value
    ...         if dt.weekday() < 5:  # weekdays
    ...             return self.product_revenue(dt - relativedelta(days=1))
    ...         # weekends
    ...         return self.product_revenue(dt - relativedelta(days=1)) * (1 + self.rate)
    ...     @child
    ...     def service_revenue(self, year: int) -> float:
    ...         return self.product_revenue(year) * 0.25
    ...     @child
    ...     def __call__(self, year: int) -> float:
    ...         return self.product_revenue(year) + self.service_revenue(year)

Now that the recursive functions are cached, we can iteratively call from the first day to any date arbitrarily far out in the future.

.. code-block:: python

    >>> initial_date = date(2020, 1, 1)
    >>> end_date = date(2025, 1, 1)
    >>> days = (end_date - initial_date).days

    >>> revenue = DailyRevenue(initial_date, 100 / 365, 0.0001)
    >>> with revenue as r:
    ...     for day in range(days + 1):
    ...         daily_rev = r.display(initial_date + relativedelta(days=day))
    
    >>> print(daily_rev)
    (('product_revenue', 0.2886530654950888), ('service_revenue', 0.0721632663737722), ('__call__', 0.360816331868861))

The functions in ``DailyRevenue`` are not pure functions. They depend on object state (initial date, value, rate, etc.).

Functions often depend on some object state. Whenever using a cached wrapper, calls should be used with a `context manager <https://docs.python.org/3/reference/compound_stmts.html#with>`_. Placing a ``Node`` in a context manager clears caches across the entire tree on entry and on exit.

The next section discusses forwarding calls between different nodes.
