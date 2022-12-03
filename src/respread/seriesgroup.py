from __future__ import annotations
from typing import Any, Callable, Dict, Tuple

from respread.series import _SERIES_CACHE, SeriesType, is_series


class SeriesGroup(SeriesType):
    
    def __init__(self, parent: SeriesGroup | None = None, children: Dict[str, Callable] | None = None) -> None:
        super().__init__()
        setattr(self, _SERIES_CACHE, {})
        self.parent = parent
        self._children = tuple()
        self._add_series_to_children()
        if children:
            for name, child in children:
                self.add_child(name, child)
    
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
        """Add child. Will overwrite any child with the same name. `index=None` (default) will add to the end."""
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
    
    def __call__(self, *args: Any, **kwds: Any) -> Tuple:
        return tuple((child, getattr(self, child)(*args, **kwds)) for child in self.children)
    
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
