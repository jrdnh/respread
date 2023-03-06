.. _grouping_functions:

*****************************
Grouping functions with Nodes
*****************************

``respread`` organizes functions into nodes. A ``Node`` class (or subclass) holds a tuple of attribute names in its ``children`` property indicating which attributes are children. Adding a child is as simple adding an attribute to a node and adding its attribute name to ``children``.

.. code-block:: python
    :emphasize-lines: 8, 9

    >>> from respread import Node

    >>> def product_revenue(year: int) -> float:
    ...     # 100 in 2020, growing 8% thereafter
    ...     return 100 * 1.08 ** (year - 2020)
    
    >>> revenue = Node()
    >>> revenue.product_revenue = product_revenue
    >>> revenue.children = ('product_revenue',)

    >>> revenue.children
    ('product_revenue',)
    >>> revenue.product_revenue(2021)
    108.0

Rather than creating ``Node`` instances and adding child functions individually, you can define custom ``Node`` subclasses with logical groupings of functions.

Functions defined inside the same class can easily reference eachother. For example, the service revenue function is projected as a percentage of product revenue. It can reference the product revenue function through the shared class namespace accessed by ``self``.

Functions with the ``@child`` decorator are automatically added as children at initialization (in other words, their attributes names are added to the ``children`` property automatically).

.. code-block:: python
    :emphasize-lines: 4, 7, 9

    >>> from respread import child

    >>> class Revenue(Node):
    ...     @child
    ...     def product_revenue(self, year: int) -> float:
    ...         return 100 * 1.08 ** (year - 2020)
    ...     @child
    ...     def service_revenue(self, year: int) -> float:
    ...         return self.product_revenue(year) * 0.25
    
    >>> revenue = Revenue()

    >>> revenue.children
    ('product_revenue', 'service_revenue')
    >>> revenue.service_revenue(2020)
    25.0

Children are regular attributes. They can still be accessed and called through regular dot notation.

.. code-block:: python

    >>> hasattr(revenue, 'product_revenue') and hasattr(revenue, 'service_revenue')
    True

The next section describes how you can stack ``Nodes`` into complex models and navigate their structures.
