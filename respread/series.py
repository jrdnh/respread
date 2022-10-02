from __future__ import annotations
from copy import deepcopy
from functools import cache
from itertools import chain
from types import MethodType
from typing import Any, Callable, List


class SeriesIterator:
    """
    Eagerly builds chained iterators returning `((parent.key, child.key), <method_series>)`
    """
    def __init__(self, series) -> None:
        self.key = series.key
        self.child_iterators = []
        for c in series.children:
            try:
                self.child_iterators.append(iter(c))
            except TypeError:  # if c doesn't define an `__iter__` method, `iter(c)` returns a TypeError
                self.child_iterators.append(iter([((c.key,), c)]))
        self.iterators = chain.from_iterable(self.child_iterators)
    
    def __next__(self):
        v = next(self.iterators)
        return ((self.key, *v[0]), v[1])
    
    def __iter__(self):
        return self


def _get_sub_items(key):
    if isinstance(key, str):
        return [key]
    
    try:
        items = []
        length = key.__len__()
        for i in range(0, length):
            items.append(key[i])
        return items
    except AttributeError:
        return [key]


def _parse_key(key):
    if isinstance(key, str):
        return [[key]]
    
    # first level
    try:
        items = []
        length = key.__len__()
        for i in range(0, length):
            items.append(_get_sub_items(key[i]))
            
    except AttributeError:
        return [[key]]
    
    return items


class Series:
    
    _internal_names: list[str] = ['children', 'id', 'key', 'parent']
    
    def __init__(self, key: str = None) -> None:
        self.children = []
        self.id = id(self)
        self.key = key
        self.parent = None
        self._init_funcs()
    
    def _init_funcs(self):
        """Add series methods to children array"""
        bases = type(self).__mro__
        
        for base in bases:
            for attr in base.__dict__.values():
                if hasattr(attr, 'is_series'):
                    self.children.append(attr.bind(self))
    
    def __call__(self, *args, **kwds):
        # return SeriesCallIterator(children_iterator, *args, **kwargs)
        return [s[1](*args, **kwds) for s in iter(self)]
    
    def names(self, full_path=True, sep='.'):
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
    
    def bind(self, new_parent, key=None):
        copy = self.__deepcopy__()
        copy.parent = new_parent
        if key is not None:
            copy.key = key
        return copy
    
    def describe(self) -> str:
        num_children = len(self.children)
        rep = f"{type(self).__qualname__} object '{str(self.key)}' {id(self)} with {num_children} "
        if num_children == 0:
            print(rep + 'children: None')
        if num_children == 1:
            rep = rep + 'child:'
            child = self.children[0]
            print(rep + f'\n{str(child.key)}: {type(child)}')
        else:
            rep = rep + 'children:'
            for child in self.children:
                rep = rep + f'\n{str(child.key)}: {type(child)}'
            print(rep)
    
    # Getting attributes/children
    def __getitem__(self, key):
        parsed_keys = _parse_key(key)[0]
        matching_children = [child for child in self.children if child.key in parsed_keys]
        if len(matching_children) == 0:
            raise KeyError(f"'{type(self).__qualname__} object does not have child with key '{key}'")
        if len(matching_children) == 1:
            return matching_children[0]
        new_series = Series()
        new_series.children = matching_children
        return new_series
    
    def __setitem__(self, key, value):
        """Currently limited to setting items at first child level"""
        if value is None:
            try:
                self.__delitem__(key)
                return
            except KeyError:
                pass
        
        parsed_keys = _parse_key(key)[0]
        
        for key in parsed_keys:
            # replace all children with matching keys
            key_matched = False
            for index, child in enumerate(self.children):
                if child.key == key:
                    if isinstance(value, MethodType):
                        func = value.__func__
                        copied_value = func.type(func.__wrapped__, key).bind(self)
                    else:
                        copied_value = deepcopy(value)
                        copied_value.key = key
                        copied_value.parent = self
                    self.children.pop(index)
                    self.children.insert(index, copied_value)
                    key_matched = True
            
            # add if no children with matching key
            if not key_matched:
                if isinstance(value, MethodType):
                    func = value.__func__
                    copied_value = func.factory.bind(self)
                else:
                    copied_value = deepcopy(value)
                    copied_value.key = key
                    copied_value.parent = self
                self.children.append(copied_value)
    
    def __delitem__(self, key):
        """Raises key error if key does not exist"""
        indexes_to_delete = []
        
        for index, child in enumerate(self.children):
            if child.key in key:
                indexes_to_delete.append(index)
        
        if len(indexes_to_delete) == 0:
            raise KeyError(f'{key}')
        
        for i in indexes_to_delete:
            del self.children[i]
    
    def __deepcopy__(self, memo=None):
        deepcopy_func = self.__deepcopy__.__func__
        self.__deepcopy__ = None
        copy = deepcopy(self, memo)
        copy.__deepcopy__ = MethodType(deepcopy_func, copy)
        
        # methods are not copied by deepcopy, manually replace
        for index, item in enumerate(copy.children):
            if isinstance(item, MethodType):
                func = item.__func__
                new_func_series = func.factory.bind(copy)
                copy.children.pop(index)
                copy.children.insert(index, new_func_series)
        
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
        After regular attribute access, try setting the name for children with matching keys
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
        
        for child in self.children:
            if filter(child):
                series.append(child)
            if getattr(child, 'sub_series', False):
                series.extend(child.sub_series(filter=filter))
        
        return series
    
    def series(self, filter: Callable[[Series], bool] = None):
        return self.root().sub_series(filter=filter)
    
    # Manage caches
    def clear_cache(self, only_node=False):
        """Clear cached function values in either the entire tree or only the node and node's children"""
        if not only_node:
            self.root().clear_cache(only_node=True)
        else:
            method_children = self.sub_series(lambda s: isinstance(s, MethodType))
            for child in method_children:
                try:
                    child.cache_clear()
                except AttributeError:
                    pass
    
    def __enter__(self):
        self.clear_cache(only_node=False)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        self.clear_cache(only_node=False)
        return True


class cached_series:
    
    is_series = True
    
    def __init__(self, func, key: str = None) -> None:
        self.func = func
        self.key = key
    
    def __set_name__(self, owner, name):
        if self.key is None:
            self.key = name
    
    def __get__(self, obj, cls=None):
        """
        If obj has an array attribute "children", return the item with `.id == id(self)`
        If no object in the array meets the condition, create a bound and cached version
        of the func (with id == id(self)) and append to the array
        If `obj == None`, return self
        """
        if (obj is not None) and (hasattr(obj, 'children')):
            for item in obj.children:
                if getattr(item, 'id') == id(self):
                    return item
            
            # If no object in the array has the matching id, create and append cached method
            cached_method = self.bind(obj)
            obj.children.append(cached_method)
            return cached_method
        
        return self
    
    def bind(self, obj):
            cached_func = cache(self.func)
            cached_func.id = id(self)
            cached_func.key = self.key
            cached_func.factory = self
            cached_method = MethodType(cached_func, obj)
            return cached_method
    
    @classmethod
    def series_sum(cls, series: List[str]):
        def func(self, *args, **kwds):
            return sum([getattr(self, name)(*args, **kwds) for name in series])
        
        return cls(func)
