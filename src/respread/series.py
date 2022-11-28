from __future__ import annotations
from copy import deepcopy
from functools import cache
from types import MethodType
from typing import Any, Callable, Generic, List, ParamSpec, TypeVar


SeriesType = TypeVar('SeriesType', bound='Series')


class SeriesIterator:
    """
    Builds chained iterators returning `((first_child_key, second_child_key, ...), leaf_callable)`.
    The iterator chain is built eagerly (adding or removing items from the Series will not add or 
    remove items from the iterator), but callables are evaluated lazily.
    """
    def __init__(self, series) -> None:
        self.child_iterators = []
        for k, c in series.children.items():
            try:
                sub_children = list(iter(c))  # if c doesn't define an `__iter__` method, `iter(c)` returns a TypeError
                for (sub_k, sub_c) in sub_children:  # will raise a TypeError or ValueError if can't unpact (depending in element is too short/not unpackable or too long)
                    self.child_iterators.append(((k, *sub_k), sub_c))
            except TypeError:
                self.child_iterators.append(((k,), c))
        self.iterator = iter(self.child_iterators)
    
    def __next__(self):
        return next(self.iterator)
    
    def __iter__(self):
        return self


class Series:
    
    _internal_names: list[str] = ['children', 'id', 'parent']
    
    def __init__(self, parent: Series = None, children: dict = None) -> None:
        if parent is not None:
            self.parent = parent
        else:
            self.parent = None
        if children is not None:
            self.children = children
        else:
            self.children = {}
        self._init_children()
    
    def _init_children(self):
        """Add series methods to children dict.
        Add in reverse MRO (subclasses override super class definitions)."""
        bases = reversed(type(self).__mro__)
        
        for base in bases:
            for attr in base.__dict__.values():
                if hasattr(attr, 'is_series'):
                    self.children[attr.key] = attr.bind(self)
    
    def __call__(self, *args, **kwds):
        return [s[1](*args, **kwds) for s in iter(self)]
    
    def names(self, full_path: bool = True, sep: str = '.'):
        """
        Keys of children method series as strings
        If keys are not strings, will try to convert using `str(key)`
        `full_path` concatenates keys of all interim series
        """
        series_iterator = iter(self)
        if full_path:
            return [sep.join((str(n) for n in s[0])) for s in series_iterator]
        return [str(i[0][-1]) for i in series_iterator]
    
    def items(self, *args, **kwds):
        """
        List of `("full_path_keys_as_str", value)` tuples for all children method series
        """
        return [('.'.join((str(n) for n in s[0])), s[1](*args, **kwds)) for s in iter(self)]
    
    def __iter__(self):
        return SeriesIterator(self)
    
    def bind(self, new_parent: SeriesType) -> SeriesType:
        """Copy and """
        copy = self.__deepcopy__()
        copy.parent = new_parent
        return copy
    
    def describe(self) -> str:
        num_children = len(self.children)
        rep = f"{type(self).__qualname__} object {id(self)} with {num_children} "
        if num_children == 0:
            print(rep + 'children: None')
        if num_children == 1:
            rep = rep + 'child:'
        else:
            rep = rep + 'children:'
        for key, child in self.children.items():
            rep = rep + f'\n{str(key)}: {type(child)}'
        print(rep)
    
    # Getting attributes/children
    def __getitem__(self, key):
        try:
            return self.children.get(key)
        except KeyError:
            raise KeyError(f"'{type(self).__qualname__} object does not have child with key '{key}'")
    
    def __setitem__(self, key, value):
        if value is None:
            self.__delitem__(key)
        self.children.update({key: value})
        # if isinstance(value, MethodType) and (value.__self__ == self):
        #     func = value.__func__
        #     try:
        #         copied_value = func.factory(func.__wrapped__, key).bind(self)
        #     except:
        #         copied_value = MethodType(func, self)
        # else:
        #     copied_value = deepcopy(value)
        #     copied_value.parent = self
        
        # self.children.update({key: copied_value})
    
    def __delitem__(self, key):
        """Raises key error if key does not exist"""
        del self.children[key]
    
    def __deepcopy__(self, memo=None):
        deepcopy_func = self.__deepcopy__.__func__
        self.__deepcopy__ = None
        copy = deepcopy(self, memo)
        copy.__deepcopy__ = MethodType(deepcopy_func, copy)
        
        # methods are not copied by deepcopy, manually replace and bind to self
        # if method's __self__ attr is self, rebind to the copy
        for key, item in copy.children.items():
            if isinstance(item, MethodType) and (item.__self__ == self):
                func = item.__func__
                try:
                    new_func_series = func.factory.bind(copy)
                except AttributeError:
                    new_func_series = MethodType(func, copy)
                copy.children.update({key, new_func_series})
        
        return copy
    
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name in children keys
        This allows simpler access to children for interactive use.
        """
        # try regular attribute access first
        try:
            return object.__getattribute__(self, name)
        except AttributeError as e:
            pass
        
        # check if reserved name that isn't available
        # note this matches `__setattr__`
        # e.g. in initialization
        if name in self._internal_names:
            raise AttributeError(f"'{type(self).__qualname__}' object has no attribute '{name}'")
        
        # return any matching children
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__qualname__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        After regular attribute access, try setting the name for children with matching keys.
        Only sets objects that identify as series to children (`Series` class or `.is_series == True`)
        so that attributes can still be added to `self.__dict__`
        This allows simpler access to children for interactive use.
        """
        # this pattern mirrors pandas
        # first try regular attribute access via __getattribute__
        # i.e. obj.__getattribute__ will fail if attr doesn't exist
        try:
            object.__getattribute__(self, name)
            return object.__setattr__(self, name, value)
        except AttributeError as e:
            pass
        
        # regular assignment if internal name that is reserved but may not be assigned yet
        # note this matches `__getattr__`
        # e.g. in initialization
        if name in self._internal_names:
            return super().__setattr__(name, value )
        
        # try adding item as a child if value is a series
        if isinstance(value, Series) or getattr(value, 'is_series', False):
            try: 
                self[name] = value
                return
            except:
                pass
        
        super().__setattr__(name, value)
    
    # Navigate tree
    def root(self):
        if self.parent is None:
            return self
        return self.parent.root()
    
    def sub_series(self, filter: Callable[[Series], bool] = None):
        """Return all leaf series if filter is `None`, else return all leaves and nodes that satisfy the filter"""
        if filter is None:
            filter = lambda s: isinstance(s, MethodType)
        series = []
        
        for child in self.children.values():
            if filter(child):
                series.append(child)
            if getattr(child, 'sub_series', False):
                series.extend(child.sub_series(filter=filter))
        
        return series
    
    def series(self, filter: Callable[[Series], bool] = None):
        return self.root().sub_series(filter=filter)
    
    # Manage caches
    def clear_cache(self, node_only=False):
        """Clear cached function values in either the entire tree or only the node and node's children"""
        if not node_only:
            self.root().clear_cache(node_only=True)
        else:
            method_children = self.sub_series(lambda s: isinstance(s, MethodType))
            for child in method_children:
                try:
                    child.cache_clear()
                except AttributeError:
                    pass
    
    def __enter__(self):
        self.clear_cache(node_only=False)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        self.clear_cache(node_only=False)
        return True


_T = TypeVar("_T")
_P = ParamSpec("_P")


class cached_series(Generic[_P, _T]):
    
    is_series = True
    
    def __init__(self, func: Callable[_P, _T], key: str = None) -> None:
        self.func = func
        self.key = key
    
    def __set_name__(self, owner, name):
        if self.key is None:
            self.key = name
    
    def __get__(self, obj, cls=None) -> Callable[_P, _T]:
        """
        If obj has an array attribute "children", return the item with `.id == id(self)`
        If no object in the array meets the condition, create a bound and cached version
        of the func (with id == id(self)) and append to the array
        If `obj == None`, return self
        """
        if (obj is not None) and (hasattr(obj, 'children')):
            for item in obj.children.values():
                if getattr(item, 'series_id', None) == id(self):
                    return item
            
            # If no object in the array has the matching id, create cached method
            cached_method = self.bind(obj)
            return cached_method
        
        return self
    
    def bind(self, obj):
        cached_func = cache(self.func)
        cached_func.series_id = id(self)
        cached_func.factory = self
        cached_method = MethodType(cached_func, obj)
        return cached_method
    
    @classmethod
    def series_sum(cls, series: List[str]):
        def func(self, *args, **kwds):
            return sum([getattr(self, name)(*args, **kwds) for name in series])
        
        return cls(func)
    
    @classmethod
    def recurive_growth(cls, rate, initial_val, initial_period=0, period_name='period'):
        series = cls(None)  # cached_series with temp func placeholder
        
        def func(self, *args, **kwds):
            try:
                period = kwds.pop('period')
            except KeyError:
                raise ValueError(f'Must included named period argument "{period_name}"')
            if period < initial_period:
                return None
            if period == initial_period:
                return initial_val
            # obj key should be set before func is ever called
            prior_val = getattr(self, series.key)(*args, **{period_name: period - 1}, **kwds)
            return prior_val * (1 + rate)
        
        series.func = func
        return series
