# respread
Build composite cash flow models.

## Install
Install from GitHub.

```sh
pip install git+https://github.com/jordanhitchcock/respread.git
```

## Getting Started
`respread` provides organization for building hierachical model components, object-level caching to improve performance, and additional utilities for dealing with dates.

### `Series`
`Series` objects group callables into components by holding children callables in the `.children` attribute. Calling the `Series` calls each child with the same arguements and returns a list of their responses. 

```python
from respread import Series

describe_list = Series()
describe_list.children = [len, lambda l: None in l]
describe_list([2, 2, 8])
```
Output:
```python
[3, FALSE]
```
Since `Series` are callables themselves, they can be nested in other `Series` creating a hierarchy of function groupings.
```python
describe_int_list = Series()
describe_int_list.children = [describe_list, min, lambda l: sum(l) / len(l), max]
describe_int_list([2, 2, 8])
```
Output:
```python
[3, FALSE, 2, 6, 8]
```


### `cached_series`

`Series` instances will add any methods wrapped with the `cached_series` decorator at initialization. 

Functions built by the `cached_series` decorator use functool's `cache` wrapper to store values. Caching improves performance in many cases. It also minimizes the impact of Python's recursion limitaions by enabling iterative calculations. 

Additionally, wrapped functions have a `key` attribute. `Series` objects will inspect children with `.key` attributes for displaying names, indexing, and accessing through dot notation.

```python
from respread import cached_series

class Account(Series):
    @cached_series
    def starting_balance(self, period):
        return 100 if period <= 0 else self.ending_balance(period - 1)
    
    @cached_series
    def accrual(self, period):
        return self.starting_balance(period) * 0.01
    
    @cached_series
    def ending_balance(self, period):
        return self.starting_balance(period) + self.accrual(period)

acct = Account(key='my_account')
acct(120)
acct.ending_balance(120)
acct['ending_balance'](120)
acct.items(120)
```
Output:
```python
[330.03868945736684, 3.3003868945736685, 333.3390763519405]
333.3390763519405
333.3390763519405
[('my_account.period_starting_balance', 330.03868945736684), ('my_account.accrued_amount', 3.3003868945736685), ('my_account.period_ending_balance', 333.3390763519405)]
```

Caches are on a per-`Series` basis which means that each instance of `Account` class have its own cache for each wrapped function. Placing a `Series` in a context manager will clear any cached children functions on both entry and exit.

```python
acct_a = Account(key='a')
acct_b = Account(key='b')

with acct_a as a:
    _ = a(100)
    print(f'acct_a cache info: {a.period_starting_balance.cache_info()}')
    print(f'acct_b cache info: {acct_b.period_starting_balance.cache_info()}')

print(f'acct_a cache info after exit: {acct_a.period_starting_balance.cache_info()}')
```
Output:
```python
acct_a cache info: CacheInfo(hits=102, misses=101, maxsize=None, currsize=101)
acct_b cache info: CacheInfo(hits=0, misses=0, maxsize=None, currsize=0)
acct_a cache info after exit: CacheInfo(hits=0, misses=0, maxsize=None, currsize=0)
```

### Detailed description of `cached_series`

`cached_series` is a data descriptor that must be initialized with a function. When it's `__get__` method is called, it will try to get the first matching function from the calling object's list of `.children`. If the calling object doesn't have a `.children` attribute (for example, it isn't a `Series` object), the `cached_series` will return itself. If the calling object does have a `.children` list but the the list doesn't have a matching function, the `cached_series` will return a `MethodType` bound to the calling object and wrapped in a `functools.cache`.

Durinig initialization, `Series` objects will call any `cached_series` attributes. This means that their `.children` list will contain all bound and cached methods from the class definition. Accessing wrapped methods using dot notation will return the object stored in the `.children` list (unless the list is modified).

The order that methods appear in `.children` follows the order of class definition and the MRO for any subclasses. You can specify the order 



[If wrap with MethodType and then cache, does that help at all?]
