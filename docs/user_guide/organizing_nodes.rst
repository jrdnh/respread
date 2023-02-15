.. _organizing_nodes:

***************************
Organizing Nodes into trees
***************************

``Node`` objects can be callables themselves by implementing the special `__call__ <https://docs.python.org/3/reference/datamodel.html#object.__call__>`_ method.

Consider a node representing an operating statement model. The node should return income for the period when it is called. Revenue and expense calculations should be broken out into their own functions so they can be examined individually.

.. code-block:: python

    >>> class OperatingStatement:
    ...     def revenue(self, year: int) -> float:
    ...         return 100
    ... 
    ...     def expenses(self, year: int) -> float:
    ...         return self.revenue(year) * -0.5
    ... 
    ...     def __call__(self, year: int) -> float:
    ...         return self.revenue(year) + self.expenses(year)

    >>> os = OperatingStatement()
    >>> os(2020)
    50.0

This simplistic model has a few problems.

* Updateing even a single line requires redefining the entire class
* As the revenue and expense calculations become more complex, so will the class definition
* It is difficult to examine revenue and expense sub-detail at the same time

Since ``Node`` objects can be callable, they can be nested to create modular structures. 

The revenue calculcations in ``OperatingStatement`` could be broken out into a separate nodes similar to the ``Revenue`` class from the previous section.

.. code-block:: python
    :emphasize-lines: 9, 10, 13, 14, 15, 16, 21, 22

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

    >>> class OperatingStatement(Node):
    ...     def __init__(self, revenue: Revenue):
    ...         super().__init__()
    ...         self.revenue = revenue
    ...         self.children = ('revenue', *self.children[:-1])
    ...     @child
    ...     def expenses(self, year: int) -> float:
    ...         return self.revenue(year) * -0.5
    ...     @child
    ...     def __call__(self, year: int) -> float:
    ...         return self.revenue(year) + self.expenses(year)

    >>> os = OperatingStatement(Revenue())
    >>> os(2020)
    62.5
    >>> os.revenue(2020)
    125.0

In addition to abstracting the revenue calculations out of the operating statement model, inheriting from ``Node`` adds transparency to the structure. ``Node`` classes have several methods that make it easier to examine structure details.

A collection of name-value pairs can be produced with the ``items(*args, **kwargs)`` or ``display(*args, **kwargs)`` functions. Both functions will call all children, including nested children, with the same function arguments.

.. code-block:: python

    >>> os.items(2020)
    ((('revenue', 'product_revenue'), 100.0), (('revenue', 'service_revenue'), 25.0), (('revenue', '__call__'), 125.0), (('expenses',), -62.5), (('__call__',), 62.5))
    >>> os.display(2020)
    (('revenue.product_revenue', 100.0), ('revenue.service_revenue', 25.0), ('revenue.__call__', 125.0), ('expenses', -62.5), ('__call__', 62.5))

``items`` returns tuples of attribute names with a separate element for each level of the hierarchy. For example, the product revenue function is nested under its revenue node parent, so it shows up as ``('revenue', 'product_revenue')``.

``display`` is similar, except it concatenates names with a period.


Collections of just the values or names can be retrieved as well.

.. code-block:: python

    >>> os.names()
    ('revenue.product_revenue', 'revenue.service_revenue', 'revenue.__call__', 'expenses', '__call__')
    >>> os.values(2020)
    (100.0, 25.0, 125.0, -62.5, 62.5)

Creating collections of values makes it easy to generate panels of detailed data. Using the operating statement model, the snippet below generates line-item projections from 2020 to 2025.

.. code-block:: python

    >>> import pandas as pd
    >>> years = range(2020, 2026)

    >>> pd.DataFrame([os.values(yr) for yr in years], columns=os.names(), index=years).T
                            2020   2021    2022      2023        2024        2025
    revenue.product_revenue  100.0  108.0  116.64  125.9712  136.048896  146.932808
    revenue.service_revenue   25.0   27.0   29.16   31.4928   34.012224   36.733202
    revenue.__call__         125.0  135.0  145.80  157.4640  170.061120  183.666010
    expenses                 -62.5  -67.5  -72.90  -78.7320  -85.030560  -91.833005
    __call__                  62.5   67.5   72.90   78.7320   85.030560   91.833005

Elements appear based on their order in the node's ``children`` property. By default, children are added based on the order they appear in the class definition.

You can change the order by re-assignment to the ``children`` property. In the ``OperatingStatement`` class definition, the children are reordered so that revenue appears first. The reordering happens by reassignment in the line ``self.children = ('revenue', *self.children[:-1])``.

The next section builds out a node class for operating expenses.
