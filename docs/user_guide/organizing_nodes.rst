.. _organizing_nodes:

***************************
Organizing Nodes into trees
***************************

``Node`` objects can be callables themselves by implementing the special `__call__ <https://docs.python.org/3/reference/datamodel.html#object.__call__>` method.

Consider a model for an operating statement. It should return income for the period when it is called. Revenue and expense calculation are broken up into their own methods.

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

This model has a few problems.

* Changing even a single line of the model requires redefining the entire class
* As the revenue and expense calculations become more complex, so will the class definition
* It is difficult to calculate and export the values from all the methods at the same time

Since ``Node`` objects can be callable, the can be nested to create modular structures. 

The revenue calculcations in ``OperatingStatement`` could be broken out into a separate node similar to the ``Revenue`` class from the previous section.

.. code-block:: python
    :emphasize-lines: 2, 5, 8, 9, 12, 13, 14, 15, 16, 19

    >>> class Revenue(Node):
    ...     @child
    ...     def product_revenue(self, year: int) -> float:
    ...         return 100 * math.exp((year - 2020) * 0.08)
    ...     @child
    ...     def service_revenue(self, year: int) -> float:
    ...         return self.product_revenue(year) * 0.25
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

In addition to abstracting the revenue model out of the operating statement model, inheriting from ``Node`` adds transparency to the structure. ``Node`` has several classes that make it easier to examine the structure and call multiple functions at the same time.

A collection of name-value pairs can be produced with the ``items(*args, **kwargs)`` or ``display(*args, **kwargs)`` functions. Both functions will call all children with the same function arguments.

.. code-block:: python

    >>> os.items(2020)
    ((('revenue', 'product_revenue'), 100.0), (('revenue', 'service_revenue'), 25.0), (('expense',), -62.5), (('__call__',), 62.5))
    >>> os.display(2020)
    (('revenue.product_revenue', 100.0), ('revenue.service_revenue', 25.0), ('expense', -62.5), ('__call__', 62.5))

``items`` returns tuples of attribute names with a separate element for each level of the hierarchy. For example, the product revenue function is nested under its revenue node parent, so it shows up as ``('revenue', 'product_revenue')``.

``display`` is similar, except it concatenates names with a period.


Collections of just the values or names can be retrieved as well.

.. code-block:: python

    >>> os.names()
    ('revenue.product_revenue', 'revenue.service_revenue', 'expense', '__call__')
    >>> os.values(2020)
    (100.0, 25.0, -62.5, 62.5)

Creating collections of values makes it easy to generate panels of detailed data. Using the operating statement model, the snippet below generates line-item projections from 2020 to 2025.

.. code-block:: python

    >>> import pandas as pd
    >>> years = range(2020, 2026)

    >>> pd.DataFrame([os.values(yr) for yr in years], columns=os.names(), index=years).T
                            2020        2021  ...        2024        2025
    revenue.product_revenue  100.0  108.328707  ...  137.712776  149.182470
    revenue.service_revenue   25.0   27.082177  ...   34.428194   37.295617
    revenue.__call__         125.0  135.410883  ...  172.140971  186.478087
    expenses                 -62.5  -67.705442  ...  -86.070485  -93.239044
    __call__                  62.5   67.705442  ...   86.070485   93.239044

Elements appear based on their order in the node's ``children`` property. By default, children are added based on the order they appear in the class definition.

You can change the order by re-assignment to the ``children`` property. In the ``OperatingStatement`` definition, the children are re-assigned with revenue added as the first child and removed as the last in the line ``self.children = ('revenue', *self.children[:-1])``.



The next section builds out a node class for operating expenses.
