from __future__ import annotations
from types import MethodType
from typing import Any, Callable

from respread.child import _CHILD_CACHE, ComponentType, is_component

from typing import Generic, TypeVar
_RootType = TypeVar('_RootType', bound='Node', covariant=True)
_ParentType = TypeVar('_ParentType', bound='Node', covariant=True)


class Node(ComponentType, Generic[_RootType, _ParentType]):
    """
    Composite container type for children callables.
    
    The `children` property holds the names of attributes considered children of the `Node`.
    Calling a `Node` object will propogate the call to each child attribute and return
    a tuple with the result from each child.
    
    Any object added to a `Node`, whether through the class definition or during/after initialization,
    that has a property `is_component` set to `True` will automatically have its name added to the `children` list.
    
    `Node` objects are of type `ComponentType` themselves and can be nested to create callable tree structures.
    """
    
    def __init__(self, parent: _ParentType | None = None, children: dict[str, Callable] | None = None) -> None:
        super().__init__()
        setattr(self, _CHILD_CACHE, {})
        self.parent = parent
        self._children = tuple()
        if children:
            for name, child_ in children.items():
                self.add_child(name, child_)
        self._add_child_to_children()
    
    # ---------------------------------
    # Manage children and parents
    def set_parent(self, parent: _ParentType | None):
        """Set parent and return self."""
        self.parent = parent
        return self
        
    def _add_child_to_children(self):
        """Initialize `._children` with child attrs in reverse MRO (subclasses override super class definitions)."""
        bases = reversed(type(self).__mro__)
        
        child_attrs = {}
        for base in bases:
            for key, attr in base.__dict__.items():
                if is_component(attr):
                    child_attrs[key] = attr
        self._children = tuple([*self._children, *child_attrs.keys()])
    
    def _get_children(self):
        """Managed property with tuple of children attributes."""
        return self._children
    
    def _set_children(self, new_children: tuple[str]):
        for child_ in new_children:
            if not hasattr(self, child_):
                raise ValueError(f"Cannot find attribute '{child_}' for object {self}")
        self._children = tuple(new_children)
    
    children = property(
        fget=_get_children,
        fset=_set_children
    )
    
    def add_child(self, name: str, new_child: Callable, index: int = None):
        """
        Add or update child. 
        
        If the attribute already exists, overwrites the attribute value. If `index` is specified, moves the 
        child name to the specified index.
        
        If the attribute does not already exist, add the value as an attribute and add `name` to `children`. 
        Adds the child at the index specified or to the end if `index` is `None` (default).

        `new_child` will be added as a child regardless of whether it has property type `is_component` of `True`.
        """
        super().__setattr__(name, new_child)  # call on super to avoid circular reference with self.__setattr__
        if index is not None:
            # remove any occurence(s) of `name` before adding name at index
            new_children = [c for c in self.children if c != name]
            new_children.insert(index, name)
            self.children = new_children
        elif name not in self.children:
            self.children = tuple([*self.children, name])
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        if (__name != 'parent') and is_component(__value):
            return self.add_child(__name, __value)
        return super().__setattr__(__name, __value)
    
    def __delattr__(self, __name: str) -> None:
        if __name in self.children:
            self.children = (c for c in self.children if c != __name)
        return super().__delattr__(__name)
    
    @property
    def root(self) -> _RootType:
        """Calculated property for the root node of the structure."""
        if self.parent is not None:
            return self.parent.root
        return self
    
    def attr_above(self, attr_name: str):
        """
        Return first instance attribute `attr_name` above the current node.
        
        Return ValueError if `attr_name` is not an attribute name for any parent above the current object.
        """
        if self.parent is None:
            raise ValueError(f'No attribute "{attr_name}" above object')
        try:
            return getattr(self.parent, attr_name)
        except AttributeError:
            return self.parent.attr_above(attr_name)
    
    # ---------------------------------
    # Callable
    def display(self, *args: Any, **kwds: Any) -> tuple[str, Any]:
        """
        Tuple of ``(name, value)`` for leaf functionswhere the name is the child path concatenated by periods and the 
        value is the leaf value with arguments propogated. 
        
        Any exceptions raised will be ignored and replaced with ``None``.

        Useful for displaying results where some parameter values are not valid for all children.
        """
        results = []
        for name, child_ in iter(self):
            try:
                results.append(('.'.join(name), child_(*args, **kwds)))
            except:
                results.append(('.'.join(name), None))
        return tuple(results)
    
    def items(self, *args: Any, **kwds: Any) -> tuple:
        """Tuple of ``((child_names,), result)`` pairs with the result of calling all children in or below the node."""
        return tuple((name, child_(*args, **kwds)) for name, child_ in iter(self))
    
    def values(self, *args: Any, **kwds: Any) -> tuple:
        """Tuple of values of leaf function results. Args and keywords propogated to all leafs."""
        return tuple(child_(*args, **kwds) for name, child_ in iter(self))
    
    def names(self, sep='.'):
        """Full names of children, concatenated by `sep` (defaults to '.')."""
        return tuple(str(sep).join(name) for name, _ in iter(self))
    
    def __iter__(self) -> NodeIterator:
        """Iterate over ``((child_names,), child)`` for each child in or below the node."""
        return NodeIterator(self)
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.values(*args, **kwds)
    
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
            getattr(self, _CHILD_CACHE).clear()
            # try children
            for child_name in self.children:
                child_ = getattr(self, child_name)
                try:
                    child_.cache_clear()
                except AttributeError:
                    pass
    
    def __enter__(self):
        self.cache_clear(all_nodes=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        self.cache_clear(all_nodes=True)


class DynamicNodeMeta(type):
    """
    Metaclass that adds class annotations to `__dir__` method.

    Autocompleters may use `dir` to determine valid completion snippets.
    """
    
    def __dir__(obj):
        fields = type.__dir__(obj) + list(obj.__annotations__.keys())
        return sorted(fields)


class DynamicNode(Node[_RootType, _ParentType], metaclass=DynamicNodeMeta):
    """
    Node subclass that creates children as they are accessed.
    
    Creating child at runtime allows users to define callable objects
    that depend on the shape of input data. This is helpful when the user
    either don't know the shape of the data ahead of time or doesn't want
    to define many repetitive classes that may change frequently as the
    data change.
    
    Class annotations for each expected child child may be necessary for
    autocompleters that use te `dir` function. Annotations may improve
    the development experience but do not affect functionality.
    
    Subclasses should override the `child_factory` function to define
    how the class should respond to attributes that don't exist in the
    class. For example, the object might return the value from a 
    dataframe or network request.
    
    
    Examples
    --------
    >>> historical_revenue = {
    ...     'product_revenue': {
    ...         2020: 50_000_000,
    ...         2021: 60_000_000
    ...     },
    ...     'service_revenue': {
    ...         2020: 25_000_000,
    ...         2021: 30_000_000
    ...     }
    ... }
    
    >>> class Revenue(DynamicNode):
    ... 
    ...     product_revenue: Callable[[int], int]
    ...     service_revenue: Callable[[int], int]
    ... 
    ...     def __init__(self, historical_revenue, parent=None, children=None) -> None:
    ...         super().__init__(parent, children)
    ...         self.historical_revenue = historical_revenue
    ... 
    ...     def child_factory(self, name: str):
    ...         if name not in self.historical_revenue.keys():
    ...             raise ValueError(f'{name} not in data')
    ...         def child_func(self, year):
    ...             revenue_data = self.historical_revenue.get(name)
    ...             return revenue_data[year]
    ...         return cached_child(child_func)
    ... 
    ...     def get_derived_children(self):
    ...         return list(self.historical_revenue.keys())
    
    >>> revenue = Revenue(historical_revenue)
    >>> revenue.product_revenue(2020)
    50000000
    
    >>> revenue.subscription_revenue(2020)  # 'subscription_revenue' not in the data
    <TRACEBACK INFO>
    AttributeError: '<class '__main__.Revenue'> object does not have attribute 'subscription_revenue'
    """
    
    def __dir__(self):
        fields = super().__dir__() + list(self.__annotations__.keys())
        return sorted(fields)

    def _method_factory(self, name):
        if name not in self.get_derived_children():
            raise AttributeError(f"Attribute '{name}' does not exist for {self}")
        return MethodType(self.child_factory(name), self)
    
    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass
        
        return self._method_factory(name)
    
    def child_factory(self, name: str) -> Callable:
        """
        Function that defines result of calling non-existent attr, should be overridden.
        
        If the object does not have an attribute ``name`` and ``name`` is in 
        ``self.get_derived_children()``, this method will be called on attribute lookup.
        Concrete subclasses should return a callable for the child of ``name``. The callable
        will be bound before it is returned.
        
        Parameters
        ----------
        name : str
            Name of requested child attribute
        """
        raise NotImplementedError('Must provide concrete implementation of "child_factory".')
    
    def get_derived_children(self) -> tuple[str]:
        """
        Names of derived children attributes.
        
        Override in concrete subclasses. Should return a tuple of strings.
        Derived children names will appear as children. Attribute children 
        will appear after any derived children names.
        """
        raise NotImplementedError('Must provide concrete implementation of "get_derived_children".')
    
    def _get_children(self):
        derived_children = list(self.get_derived_children())
        attr_children = super().children
        derived_children.extend([c for c in attr_children if c not in derived_children])
        return tuple(derived_children)
    
    def _set_children(self, value):
        return super()._set_children(value)
    
    children = property(
        fget=_get_children,
        fset=_set_children
    )


class NodeIterator:
    """Iterator for `Node` returning `((child_names,), child)` for each child below the node."""
    def __init__(self, node: Node) -> None:
        self.children = []
        
        for child_name in node.children:
            child_ = getattr(node, child_name)
            if isinstance(child_, Node):
                for sub_child_name, sub_child in iter(child_):
                    self.children.append(((child_name, *sub_child_name), sub_child))
            else:
                self.children.append(((child_name,), child_))
        
        self.children_iterator = iter(self.children)
    
    def __iter__(self) -> NodeIterator:
        return self
    
    def __next__(self):
        return next(self.children_iterator)
