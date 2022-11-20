# respread
`respread` provides organization for building hierachical function groups, object-level caching that improves performance, and additional utilities for dealing with dates.


## Install

```sh
pip install git+https://github.com/jordanhitchcock/respread.git
```

## Getting Started

### `Series`
`Series` objects arrange callables into logical groupings. `Series` are callables themselves, which means they can by nested into hierarchical structures. `Series` hold children callables as key-value pairs in their `children` dictionary attribute.

The default return value of a `Series` is a list of return values generated from calling the `Series'`s children with the same arguments.

Children callables are accessable *i)* by accessing the the `children` attribute directly (`my_series.children[key]`), *ii)* indexing the `Series` object (`my_series[key]`), or *iii)* by dot notation (`my_series.key`).)

```python
from respread import Series

# Describe a list by returning its length and whether it has any `None` elements
describe_list = Series()
describe_list.children = {'length': len, 'has_none': lambda l: None in l}
print(describe_list([2, 2, 8]))  # equivalent to [c([2, 2, 8]) for c in describe_list.children.values()]
print(describe_list.has_none([1, 2, None]))
```
Output:
```python
[3, False]
True
```
Since `Series` are callables themselves, they can be nested in other `Series` creating a hierarchy of function groupings.
```python
# Extension for describing a list of ints that also returns the min, avg, and max values
describe_int_list = Series()
describe_int_list.children = {'base_desc': describe_list, 'min': min, \
    'avg': lambda l: sum(l) / len(l), 'max': max}
print(describe_int_list([2, 2, 8]))
print(describe_int_list.items([2, 2, 8]))  # `.items` returns a list of (key, result) pairs
```
Output:
```python
[3, False, 2, 4.0, 8]
[('base_desc.length', 3), ('base_desc.has_none', False), ('min', 2), ('avg', 4.0), ('max', 8)]
```


### `cached_series`

`Series` instances will add any methods wrapped with the `cached_series` decorator to the `children` dict at initialization. 

Functions built by the `cached_series` decorator use functool's `cache` wrapper to store values. Caching improves performance in many cases. It also minimizes the impact of Python's recursion limitaions by enabling iterative calculations. 

```python
from respread import cached_series

class Account(Series):
    
    def __init__(self, initial_balance, interest_rate):
        super().__init__()
        self.initial_balance = initial_balance
        self.interest_rate = interest_rate
    
    @cached_series
    def starting_balance(self, period):
        return self.initial_balance if period <= 0 else self.ending_balance(period - 1)
    
    @cached_series
    def accrual(self, period):
        return self.starting_balance(period) * self.interest_rate
    
    @cached_series
    def ending_balance(self, period):
        return self.starting_balance(period) + self.accrual(period)

acct = Account(initial_balance=100, interest_rate=0.01)
print(acct.children)
print(acct.items(120))
```
Output:
```python
{'starting_balance': <bound method Account.starting_balance of <__main__.Account object at 0x10dd53460>>, 'accrual': <bound method Account.accrual of <__main__.Account object at 0x10dd53460>>, 'ending_balance': <bound method Account.ending_balance of <__main__.Account object at 0x10dd53460>>}
[('starting_balance', 330.03868945736684), ('accrual', 3.3003868945736685), ('ending_balance', 333.3390763519405)]
```

Caches are on a per-`Series` instance basis which means that each instance of `Account` has its own cache for each wrapped function. Placing a `Series` in a context manager will clear any cached children on both entry and exit.

```python
acct_a = Account(100, 0.01)
acct_b = Account(100, 0.01)

with acct_a as a:
    _ = a(100)
    print(f'acct_a cache info: {a.starting_balance.cache_info()}')
    print(f'acct_b cache info: {acct_b.starting_balance.cache_info()}')

print(f'acct_a cache info after exit: {acct_a.starting_balance.cache_info()}')
```
Output:
```python
acct_a cache info: CacheInfo(hits=102, misses=101, maxsize=None, currsize=101)
acct_b cache info: CacheInfo(hits=0, misses=0, maxsize=None, currsize=0)
acct_a cache info after exit: CacheInfo(hits=0, misses=0, maxsize=None, currsize=0)
```

### Detailed description of `cached_series`

`cached_series` is a descriptor that must be initialized with a function. When its `__get__` method is called, it will try to get the first matching function from the calling object's `.children` dictionary. If the calling object doesn't have a `.children` attribute (for example, it isn't a `Series` object), the `cached_series` will return itself. If the calling object does have a `.children` list but the the list doesn't have a matching function, the `cached_series` will return a `MethodType` bound to the calling object and wrapped in `functools.cache`.

Durinig initialization, `Series` objects will call any `cached_series` attributes in the class definition. This means that an instance's `.children` dictionary will contain all bound and cached methods from the class definition. Accessing wrapped methods using dot notation will return the object stored in the `.children` dictionary (unless it was removed from the dictionary, in which case it will build and return a new bound and cached method).

The order that methods appear in `.children` follows the order of class definition and the MRO for any subclasses. You can specify the order at initialization by redefining the `.children` dictionary.
