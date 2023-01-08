.. _working_with_data:

*****************
Working with Data
*****************

Arrays of data, such as historical financials or future projections, are common model inputs. The ``DynamicNode`` class wraps a data object or query into a ``Node`` object that creates children functions as they are called.

Suppose we wanted to create a five year operating statement with two years of historical results and three years of projections. The DataFrames below hold historical financials and projected assumption data by year.

.. code-block:: python

    >>> import pandas as pd

    >>> historicals = (pd.DataFrame([[1000, 1150], [750, 850]],
    ...                             index=['revenue', 'expenses'],
    ...                             columns=[2020, 2021]))
    
    >>> assumptions = (pd.DataFrame([[125, 135, 145], [9.5, 9.7, 9.9], [0.75, 0.74, 0.73]],
    ...                             index=['units', 'revenue_per_unit', 'opex_pct_rev'],
    ...                             columns=[2022, 2023, 2024]))

.. code-block:: python

    >>> print(historicals)
              2020  2021
    revenue   1000  1150
    expenses   750   850

    >>> print(assumptions)
                        2022    2023    2024
    units             125.00  135.00  145.00
    revenue_per_unit    9.50    9.70    9.90
    opex_pct_rev        0.75    0.74    0.73  # operating expenses as a percent of revenue

Collecting inputs in one place separates the functions from the data and makes it easy to update the model as assumptions change.

We can add these data as line items to the model with a ``DynamicNode``. 

Concrete ``DynamicNode`` subclasses must implement two methods. 

* ``get_derived_children()`` : Override this method to return a tuple of valid children names derived from the data source.
* ``child_factory(name: str)`` : If the object does not have an existing attribute ``name`` and ``name`` is in the response of ``get_derived_children``, this method will be called. It should return a callable child for ``name``.

.. code-block:: python
    :emphasize-lines: 7, 8, 9, 10, 11, 12, 13, 14, 15

    >>> from respread import DynamicNode

    >>> class DataFrameNode(DynamicNode):
    ...     def __init__(self, df) -> None:
    ...         super().__init__()
    ...         self.df = df
    ...     def get_derived_children(self):
    ...         # valid children names are determined by the dataframe's index
    ...         return list(self.df.index)
    ...     def child_factory(self, name: str):
    ...         # create a child function that gets the 
    ...         # correct value from the dataframe
    ...         def child_func(self, year):
    ...             return self.df.loc[name].get(year, None)
    ...         return child_func

.. code-block:: python
    
    >>> historicals = DataFrameNode(historicals)
    >>> historicals.children
    ('revenue', 'expenses')

    >>> historicals.revenue(2020)
    1000
    >>> historicals.items(2020)
    ((('revenue',), 1000), (('expenses',), 750))

    >>> historicals.capital_expenditure(2020)  # invalid child name, raises AttributeError
    AttributeError: Attribute 'capital_expenditure' does not exist for <__main__.DataFrameNode object at 0x10f62bee0>

The ``DataFrameNode`` class depends entirely on its DataFrame property. Adding a new row to the DataFrame will add a new child to node where the name of the child is the row's index value.

Since the value of the DataFrame is not know until runtime, autocompletion tools have no way of knowing about children attributes.

It is possible to inform autocompleters about children by annotating the class. Annotations modify the result of calling ``dir(object)``. This populates many autocompletion tools but does not affect a node's actual children in any way.

.. code-block:: python

    >>> from typing import Callable

    >>> class Historicals(DataFrameNode):
    ...     revenue: Callable
    ...     expenses: Callable
    ...     will_not_appear_in_children: Callable

.. code-block:: python

    >>> dir(Historicals)  # autocompletion will appear for these attributes
    [..., 'expenses', ..., 'revenue', ..., 'will_not_appear_in_children']

    >>> historicals.children
    ('revenue', 'expenses')

The rest of the operating statement definition could be defined as follows.

.. code-block:: python

    >>> from respread import child, Node

    >>> class Assumptions(DataFrameNode):
    ...     units: Callable
    ...     revenue_per_unit: Callable
    ...     opex_pct_rev: Callable

    >>> class OperatingStatement(Node):
    ...     def __init__(self, assumptions: Assumptions, historicals: Historicals) -> None:
    ...         super().__init__()
    ...         cls_children = self.children
    ...         self.assumptions = assumptions.set_parent(self)
    ...         self.historicals = historicals.set_parent(self)
    ...         # set order of children
    ...         self.children = ('assumptions', 'historicals', *cls_children)
    ...     @child
    ...     def revenue(self, year):
    ...         if hist_value := self.historicals.revenue(year):
    ...             return hist_value
    ...         return self.assumptions.units(year) * self.assumptions.revenue_per_unit(year)
    ...     @child
    ...     def expenses(self, year):
    ...         if hist_value := self.historicals.expenses(year):
    ...             return hist_value
    ...         return -self.revenue(year) * self.assumptions.opex_pct_rev(year)
    ...     @child
    ...     def operating_income(self, year):
    ...         return self.revenue(year) + self.expenses(year)

    >>> pro_forma = (OperatingStatement(assumptions=Assumptions(assumptions),
    ...                                 historicals=Historicals(historicals)))

.. code-block:: python
    
    >>> yrs = range(2020, 2025)
    >>> pd.DataFrame([pro_forma(y) for y in yrs], index=yrs, columns=pro_forma.names()).T
                                    2020    2021      2022     2023      2024
    assumptions.units                NaN     NaN   125.000   135.00   145.000
    assumptions.revenue_per_unit     NaN     NaN     9.500     9.70     9.900
    assumptions.opex_pct_rev         NaN     NaN     0.750     0.74     0.730
    historicals.revenue           1000.0  1150.0       NaN      NaN       NaN
    historicals.expenses           750.0   850.0       NaN      NaN       NaN
    revenue                       1000.0  1150.0  1187.500  1309.50  1435.500
    expenses                       750.0   850.0  -890.625  -969.03 -1047.915
    operating_income              1750.0  2000.0   296.875   340.47   387.585
