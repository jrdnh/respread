from __future__ import annotations
from itertools import chain
from typing import Any, Callable, Dict, Tuple

from respread.series import _SERIES_CACHE, SeriesType, is_series


class SeriesGroup(SeriesType):
    """
    Callable container type for series.
    
    The `children` property holds the names of attributes considered children of the `SeriesGroup`.
    Calling a `SeriesGroup` object will propogate the call to each child attribute and return
    a tuple with the result from each child.
    
    Any object added to a `SeriesGroup`, whether through the class definition or during/after initialization,
    that has a property `is_series` set to `True` will automatically have its name added to the `children` list.
    
    `SeriesGroup` objects are of type `SeriesType` themselves and can be nested to create callable tree structures.
    """
    
    def __init__(self, parent: SeriesGroup | None = None, children: Dict[str, Callable] | None = None) -> None:
        super().__init__()
        setattr(self, _SERIES_CACHE, {})
        self.parent = parent
        self._children = tuple()
        self._add_series_to_children()
        if children:
            for name, child in children.items():
                self.add_child(name, child)
                try:
                    child.parent = self
                except AttributeError:
                    pass
    
    def _add_series_to_children(self):
        """Initialize `._children` with series attrs in reverse MRO (subclasses override super class definitions)."""
        bases = reversed(type(self).__mro__)
        
        series_attrs = {}
        for base in bases:
            for key, attr in base.__dict__.items():
                if is_series(attr):
                    series_attrs[key] = attr
        self.children = tuple(*self.children, series_attrs.keys())
    
    def set_parent(self, parent: SeriesGroup | None):
        """Set parent and return self."""
        self.parent = parent
        return self
    
    def attr_above(self, attr_name: str):
        """
        Return first instance attribute `attr_name` above the current node.
        
        Return ValueError if `attr_name` is not an attribute name for any parent above the current object.
        """
        if self.parent is None:
            raise ValueError(f'No attribute "{attr_name}" above object {self}')
        try:
            return getattr(self.parent, attr_name)
        except AttributeError:
            return self.parent.attr_above(attr_name)
        
    @property
    def children(self):
        return self._children
    
    @children.setter
    def children(self, new_children: Tuple[str]):
        for child in new_children:
            if not hasattr(self, child):
                raise ValueError(f'Cannot find attribute {child} for object {self}')
        self._children = tuple(new_children)
    
    def add_child(self, name: str, child: Callable, index: int = None):
        """
        Add child. 
        
        Will overwrite any child with the same name. `index=None` (default) will add to the end.
        `child` will be added as a child regardless of whether it has property type `is_series == True`.
        """
        super().__setattr__(name, child)  # call on super to avoid circular reference with self.__setattr__
        new_children = list(self.children)
        if index is None:
            self.children = tuple([*self.children, name])
        else:
            new_children.insert(index, name)
            self.children = new_children
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if (__name != 'parent') and is_series(__value):
            return self.add_child(__name, __value)
        return super().__setattr__(__name, __value)
    
    def __delattr__(self, __name: str) -> None:
        if __name in self.children:
            self.children = (child for child in self.children if child != __name)
        return super().__delattr__(__name)
    
    # ---------------------------------
    # Callable
    def __call__(self, *args: Any, **kwds: Any) -> Tuple:
        # return tuple(result for child in self.children for result in getattr(self, child)(*args, **kwds))
        return tuple(child(*args, **kwds) for name, child in iter(self))
    
    def items(self, *args: Any, **kwds: Any) -> Tuple:
        """`((child_names,), result)` for each child below the node with results from calling the child."""
        return tuple((name, child(*args, **kwds)) for name, child in iter(self))
    
    def names(self, sep='.'):
        """Full names of children, concatenated by `set` (defaults to '.')."""
        return tuple(f'{sep}'.join(name) for name, child in iter(self))
    
    def __iter__(self) -> SeriesGroupIterator:
        return SeriesGroupIterator(self)
    
    # ---------------------------------
    # Context manager and cache clear
    def cache_clear(self, all_nodes=False):
        """Clear the cache for the current node and all children (default) or entire tree."""
        # call on parent if all_nodes
        if all_nodes and self.parent:
            self.parent.cache_clear(all_nodes=True)
        # else clear own cache and call children
        else:
            # clear self's cache
            getattr(self, _SERIES_CACHE).clear()
            # try children
            for child_name in self.children:
                child = getattr(self, child_name)
                try:
                    child.cache_clear()
                except AttributeError:
                    pass
    
    def __enter__(self):
        self.cache_clear(all_nodes=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        self.cache_clear(all_nodes=True)


class SeriesGroupIterator:
    """Iterator for `SeriesGroup` returning `((child_names,), child)` for each child below the node."""
    def __init__(self, series: SeriesGroup) -> None:
        self.children = []
        
        for child_name in series.children:
            child = getattr(series, child_name)
            if isinstance(child, SeriesGroup):
                for sub_child_name, sub_child in iter(child):
                    self.children.append(((child_name, *sub_child_name), sub_child))
            else:
                self.children.append(((child_name,), child))
        
        self.children_iterator = iter(self.children)
    
    def __iter__(self) -> SeriesGroupIterator:
        return self
    
    def __next__(self):
        return next(self.children_iterator)
