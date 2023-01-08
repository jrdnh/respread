# respread

![tests](https://github.com/jrdnh/respread/actions/workflows/ci-tests.yaml/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/jrdnh/respread/branch/main/graph/badge.svg?token=NXAZZ27KED)](https://codecov.io/gh/jrdnh/respread)

`respread` is a spreadsheet alternative for end-user models. It allows users to easily build a modeling engine that can access Python's abundant statistical, computational, and networking ecosystem.

* **Leverage the full Python ecosystem**
    - Integrate statistical or AI/ML components directly into the end-user model
    - Connect to resources over the web, such as data science models, third-party data vendors, or internal corporate datastores
    - Analyze datasets that are too big or not appropriately structured for spreadsheets
* **Create reusable, test-hardened components**
* **Quickly build end-user models as part of an automated process**

`respread` organizes functions into composite hierarchies that can be reused, tested, and configured at runtime. 

It is particularly well suited for generating tabular outputs where the first axis is defined by the function (e.g. revenue, cost of goods, operating margin, etc.) and the second axis is defined by inputs to those functions (e.g. time period or operating scenario).

```python
>>> import pandas as pd
>>> from respread import cached_child, Node

>>> class Revenue(Node):
...     @cached_child
...     def product_rev(self, year):
...         return 100_000_000 if year == 2020 else self.product_rev(year - 1) * 1.1
...     @cached_child
...     def service_rev(self, year):
...         return 35_000_000 if year == 2020 else self.product_rev(year - 1) * 1.08

>>> class OperatingStatement(Node):
...     def __init__(self, revenue):
...         super().__init__(children={'revenue': revenue})
...     @cached_child
...     def operating_expenses(self, year):
...         return -sum(self.revenue(year)) * 0.65
...     @cached_child
...     def operating_income(self, year):
...         return sum(self.revenue(year)) + self.operating_expenses(year)

>>> os = OperatingStatement(revenue=Revenue())
>>> os.revenue.product_rev(2022)
121000000.00000003

>>> proj_yrs = range(2020, 2025)
>>> pd.DataFrame([os(yr) for yr in proj_yrs], index=proj_yrs, columns=os.names()).T
                            2020         2021         2022         2023         2024
revenue.product_rev  100000000.0  110000000.0  121000000.0  133100000.0  146410000.0
revenue.service_rev   35000000.0  108000000.0  118800000.0  130680000.0  143748000.0
operating_expenses   -87750000.0 -141700000.0 -155870000.0 -171457000.0 -188602700.0
operating_income      47250000.0   76300000.0   83930000.0   92323000.0  101555300.0
```

`respread` integrates data from any source into the model nodes. Separating data sources from model calculations makes it easy to update inputs. Create the model structure once, use it repeatedly for different scenarios.

```python
>>> from respread import DynamicNode

>>> data = [[50_000, 55_000, 60_000, 65_000, 70_000], 
...         [2_000, 2_005, 2_010, 2_015, 2_020]]
>>> assumption_df = pd.DataFrame(data, index=['units', 'price_per_unit'], columns=proj_yrs)

>>> class DataFrameNode(DynamicNode):
...     def __init__(self, df: pd.DataFrame):
...         super().__init__()
...         self.df = df
...     def get_derived_children(self):
...         return list(self.df.index)
...     def child_factory(self, name: str):
...         return lambda obj, yr: obj.df.loc[name].get(yr, None)

>>> assumptions = DataFrameNode(assumption_df)
>>> assumptions.units(2022)
60000

>>> pd.DataFrame([assumptions(yr) for yr in proj_yrs], 
...              index=proj_yrs, columns=assumptions.names()).T
                 2020   2021   2022   2023   2024
units           50000  55000  60000  65000  70000
price_per_unit   2000   2005   2010   2015   2020
```

-----------
## Features

* Build modular, reusable code components
* Access children nodes and functions by regular attribute dot notation
* Automatic recognition of new children elements as they are added
* Cache management for recursive or expensive calculations
* Ability to dynamically create child nodes and functions at runtime
* IDE-aware design with support for type annotations and autocompletion

Check out the documentation for additional detail on getting started and the API reference guide.

----------------
## Documentation

User and reference guides: https://jrdnh.github.io/respread/

---------------
## Installation

Requires Python 3.10 or higher. Install directly from GitHub with `pip`:

```sh
pip install git+https://github.com/jordanhitchcock/respread.git
```

The package is in alpha status and may undergo material changes.

------------------------------
## Contribute or ask questions

* Issue tracker: [https://github.com/jrdnh/respread/issues](https://github.com/jrdnh/respread/issues)
* Source code: [https://github.com/jrdnh/respread](https://github.com/jrdnh/respread)

----------
## License

The project is [licensed](./LICENSE) under the BSD-3-Clause license.