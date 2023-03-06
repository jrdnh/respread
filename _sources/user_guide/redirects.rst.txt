.. _redirects:

*****************
Redirecting calls
*****************

Redirecting calls to another function and handling errors if the target function fails is a common pattern. For example, consider the original ``Revenue`` class from previous sections.

.. code-block:: python

    >>> class Revenue(Node):
    ...     @child
    ...     def product_revenue(self, year: int) -> float:
    ...         return 100 * 1.08 ** (year - 2020)
    ...     @child
    ...     def service_revenue(self, year: int) -> float:
    ...         return self.product_revenue(year) * 0.25
    ...     @child
    ...     def __call__(self, year: int) -> float:
    ...         return self.product_revenue(year) + self.service_revenue(year)

Rather than creating one node that handles both historical and projected revenue, it would better to separate historical revenue into its own node. This makes the ``Revenue`` node portable and allows clear separation of the data components from the modeling components.

When a user requests revenue for a particular year, the model should ask the historical revenue node for revenue for that year. If the historical node has a valid data point, the historical response should be returned to the user. If the year is *after* the historical range, the historical node should raise an error indicating so. The revenue modeling node can then calculate and return the appropriate projection.

Start by creating the historical data class. The custom exception type indicates an out of bound error to the right.

.. code-block:: python

    >>> class AfterPeriodError(Exception):
    ...     pass

    >>> class Historicals(Node):
    ...     hist_product_rev = {2019: 90, 2020: 100}
    ...     hist_service_rev = {2019: 21, 2020: 24}
    ...     
    ...     @child
    ...     def product_revenue(self, year: int) -> float:
    ...         if year > max(self.hist_product_rev.keys()):
    ...             raise AfterPeriodError
    ...         return self.hist_product_rev[year]
    ...     @child
    ...     def service_revenue(self, year: int) -> float:
    ...         if year > max(self.hist_service_rev.keys()):
    ...             raise AfterPeriodError
    ...         return self.hist_service_rev[year]

    >>> historicals = Historicals()
    >>> historicals.product_revenue(2020)
    100
    >>> historicals.product_revenue(2025)
    __main__.AfterPeriodError

Requesting revenue for a year after the historical range will result in an ``AfterPeriodError``. Requesting revenue for a year prior to the historical range or of an invalid argument type will result in a typical ``KeyError``.

Next, redefine new operating statement subclass that holds a node with historical data.

.. code-block:: python

    >>> class HistOperatingStatement(OperatingStatement):
    ...     def __init__(self, historicals: Historicals, revenue: Revenue, expenses):
    ...         super().__init__(revenue, expenses)
    ...         self.historicals = historicals.set_parent(self)
    ...         self.children = ('historicals', *self.children[:-1])

Lastly, modify the ``Revenue`` class to forward calls to the historical data node.

``respread`` allows users to redirect calls between nodes using the ``@redirect`` decorator. This decorator forwards the call to the function at the specified path. If the target function raises an error caught by the decorator, then the decorated function is called.

.. code-block:: python
    :emphasize-lines: 5, 10

    >>> from respread import redirect

    >>> class Revenue(Node[HistOperatingStatement]):
    ...     @child
    ...     @redirect(('parent', 'historicals'), AfterPeriodError, append_name=True)
    ...     def product_revenue(self, year: int) -> float:
    ...         return self.product_revenue(year - 1) * 1.08
    ...     
    ...     @child
    ...     @redirect(('root', 'historicals'), AfterPeriodError, append_name=True)
    ...     def service_revenue(self, year: int) -> float:
    ...         return self.product_revenue(year) * 0.25
    ...     
    ...     @child
    ...     def __call__(self, year: int) -> float:
    ...         return self.product_revenue(year) + self.service_revenue(year)

The first argument to the ``redirect`` decorator is the path from the calling node to the target function. The path can either be relative (as in the decorator for product revenue) or absolute (as in the service revenue decorator, which starts at the root). Additionally, if ``append_name=True`` then the decorated function's name will be appended to the path.

The second argument is the exception types that should be caught. A tuple of exception types can be used if more than one exception type should be caught. If the target function raises an exception type caught by the decorator, the decorated function will be executed instead.

.. code-block:: python

    >>> os = HistOperatingStatement(historicals, Revenue(), OperatingExpenses())
    >>> os.revenue.display(2019)
    (('product_revenue', 90), ('service_revenue', 21), ('__call__', 111))
    >>> os.revenue.display(2025)
    (('product_revenue', 146.93280768000005), ('service_revenue', 36.73320192000001), ('__call__', 183.66600960000005))

When the revenue functions are called, the request will be automatically routed to the correct function. Redirections are a good way to conditionally mirror fuctions and handle exceptions as they arise.

--------

Congratulations, this concludes the **Getting started** guide! Start using ``respread`` to create new models, `ask questions <https://github.com/jrdnh/respread/discussions>`_, `file issues <https://github.com/jrdnh/respread/issues>`_, or `contribute <https://github.com/jrdnh/respread>`_!
