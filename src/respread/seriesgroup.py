from typing import Any, Tuple

from respread.series import _SERIES_CACHE, SeriesType, is_series


class SeriesGroup(SeriesType):
    
    def __init__(self) -> None:
        super().__init__()
        setattr(self, _SERIES_CACHE, {})
        self._children = tuple()
        self._add_series_to_children()
    
    def _add_series_to_children(self):
        """Initialize ._children with series attrs in reverse MRO (subclasses override super class definitions)."""
        bases = reversed(type(self).__mro__)
        
        series_attrs = {}
        for base in bases:
            for key, attr in base.__dict__.items():
                if is_series(attr):
                    series_attrs[key] = attr
        self.children = tuple(*self.children, series_attrs.keys())
    
    @property
    def children(self):
        return self._children
    
    @children.setter
    def children(self, new_children: Tuple[str]):
        for child in new_children:
            if not hasattr(self, child):
                raise ValueError(f'Cannot find attribute {child} for object {self}')
        self._children = tuple(new_children)
    
    def add_child(self, name: str, child: callable, index: int = None):
        """Add child. Will overwrite any child with the same name. index=None (default) will add to the end."""
        super().__setattr__(name, child)  # call on super to avoid circular reference with self.__setattr__
        new_children = list(self.children)
        if index is None:
            self.children = tuple([*self.children, name])
        else:
            new_children.insert(index, name)
            self.children = new_children
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if is_series(__value):
            return self.add_child(__name, __value)
        return super().__setattr__(__name, __value)
    
    def __delattr__(self, __name: str) -> None:
        if __name in self.children:
            self.children = (child for child in self.children if child != __name)
        return super().__delattr__(__name)
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return tuple((child, getattr(self, child)(*args, **kwds)) for child in self.children)
