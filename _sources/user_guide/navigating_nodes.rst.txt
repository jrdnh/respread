.. _navigating_nodes:

*********************************
Navigating nodes and type hinting
*********************************

In the previous section, revenue calculations were abstracted out into their own class. It makes sense to create another abstraction for expenses.

The expense class will consist of two functions:

i) cost of goods sold (COGS) equal to 60 percent of product revenue and 
ii) other expenses that grow at a constant rate.

The expense node is different than the revenue and operating statement nodes because it depends on a sibling node. Specifically, it depends on the product revenue function in the revenue node. 

``Node`` classes have a ``parent`` property that is expected to point to the node above. The highlighted line in the ``cogs`` definition gets the parent node (which is the root ``OperatingStatement`` node in this model) followed by its revenue and product revenue components.

.. code-block:: python
    :emphasize-lines: 4

    >>> class OperatingExpenses(Node[OperatingStatement, OperatingStatement]):
    ...     @child
    ...     def cogs(self, year: int) -> float:
    ...         return self.parent.revenue.product_revenue(year) * -0.6
    ...     @child
    ...     def other_expenses(self, year: int) -> float:
    ...         return 100 * 1.08 ** (year - 2020)
    ...     @child
    ...     def __call__(self, year: int) -> float:
    ...         return self.cogs(year) + self.other_expenses(year)

The updated operating model is below. Note that the expense object's parent is explicitly set when it is assigned during initialization. The ``set_parent`` method just sets the parent property and returns the node for a more fluent flow.

.. code-block:: python
    :emphasize-lines: 5

    >>> class OperatingStatement(Node):
    ...     def __init__(self, revenue: Revenue, expenses):
    ...         super().__init__()
    ...         self.revenue = revenue.set_parent(self)
    ...         self.expenses = expenses.set_parent(self)
    ...         self.children = ('revenue', 'expenses', '__call__')
    ...     @child
    ...     def __call__(self, year: int) -> float:
    ...         return self.revenue(year) + self.expenses(year)

    >>> os = OperatingStatement(Revenue(), OperatingExpenses())
    >>> os(2020)
    57.0
    >>> os.expenses.display(2020)
    (('cogs', -60.0), ('other_expenses', -8.0), ('__call__', -68.0))

===========================
Absolute and relative paths
===========================

The operating expense node currently sits as a direct child of the operating statement node.

::

    OperatingStatement
    ├── Revenue
    │   ├── product_revenue
    │   └── service_revenue
    └── OperatingExpenses
        ├── cogs
        └── other_expenses

However, it might be better to include operating expenses as just one component of total expenses. For example, we might want to include interest expense (a non-operating expense) in addition to operating expenses.

::

    OperatingStatement
    ...
    └── Expenses
        ├── OperatingExpenses
        │   ├── cogs
        │   └── other_expenses
        └── interest_expense

The ``OperatingExpenses`` class currently uses a relative path from itself to find ``product_revenue``. It can be modified to use an absolute path relative to the root ``OperatingStatement`` node using the ``root`` property.

.. code-block:: python
    :emphasize-lines: 4

    >>> class OperatingExpenses(Node[OperatingStatement, Node]):
    ...     @child
    ...     def cogs(self, year: int) -> float:
    ...         return self.root.revenue.product_revenue(year)
    ...     ...

Using absolute paths can make classes more resilient to nesting. No matter how deeply the operating expense node is buried, it will always find the revenue node.

==========================
Parent and root type hints
==========================

As node trees grow, it quickly gets difficult to remember the children names for each node. ``Node`` classes are `generics <https://docs.python.org/3/library/typing.html#generics>`_ with respect their parent and root types which improves type hinting and autocompletion.

Recall the first line of the original ``OperatingExpenses`` class.

.. code-block:: python

    >>> class OperatingExpenses(Node[OperatingStatement, OperatingStatement]):

The bracketed phrase does not change any runtime behavior. All it does is inform static type checkers that its parent and roots will be of type ``OperatingStatement``. It does not enforce any type checking at runtime, and any class can be set as the parent.

In the updated ``OperatingExpenses`` class, the type hints changed slightly.

.. code-block:: python

    >>> class OperatingExpenses(Node[OperatingStatement, Node]):

The first bracketed element is the root type. The second element is the parent type. We know that the root should conform to the ``OperatingStatement`` class, but since the operating expense object may be nested arbitrarily deep we can only state that it's direct parent will be some ``Node`` object.

Telling static type checkers that the parent will be an ``OperatingStatement`` object enables autocompletion in most development environments (including IPython, VS Code/Pyright, and PyCharm). The ``cogs`` function definition should receive good autcompletion and generate type hints for every element in the ``self.parent.revenue.product_revenue`` chain.