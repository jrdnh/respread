# from abc import ABC
from functools import cache
from types import MethodType
from typing import Callable, Generic, ParamSpec, TypeVar


_CHILD_CACHE = '_child_cache'
IS_COMPONENT = 'is_component'


# -----------------------------
# Helpers
def is_component(obj) -> bool:
    return getattr(obj, IS_COMPONENT, False)


ComponentType = type('ComponentType', 
                     tuple(), 
                     {IS_COMPONENT: True, '__doc__': 'Mixin base class for identifying types automatically treated as components.'})


_P = ParamSpec('_P')
_T = TypeVar('_T')


# class AbstractChild(ComponentType):
    
#     def __init__(self, func: Callable[_P, _T]) -> None:
#         super().__init__()
#         self._func = func
#         self.__name__ = func.__name__
    
#     def __set_name__(self, owner, name: str):
#         self.__name__ = name
    
#     def __get__(self, obj, cls=None):
#         if obj is None:
#             return self
#         return MethodType(self, obj)
    
#     def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
#         return self._func(*args, **kwds)


# -----------------------
# Concrete types of AbstractChild

class child(Generic[_P, _T], ComponentType):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__()
        self._func = func
        self.__name__ = func.__name__
    
    def __set_name__(self, owner, name: str):
        self.__name__ = name
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return MethodType(self, obj)
    
    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        return self._func(*args, **kwds)


class cached_child(Generic[_P, _T], ComponentType):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__()
        self._func = func
        self.__name__ = func.__name__
    
    def __set_name__(self, owner, name: str):
        self.__name__ = name
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return MethodType(self, obj)
    
    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        return self._func(*args, **kwds)
    
    @property
    def id(self):
        return hash((id(self._func), id(self)))
    
    def get_cached_func(self, owner):
        # check if the owner has a cache and the cache has a matching entry
        if ((owners_cache := getattr(owner, _CHILD_CACHE, False)) and 
            (cached_func := owners_cache.get(self.id, False))):
            return cached_func
        
        # if the owner does not have a cache, try creating one
        if not owners_cache:
            try:
                setattr(owner, _CHILD_CACHE, {})
            except:
                raise ValueError(f'Could not create a cache for {self} at object {owner}')
        
        # created new cached func and save to owner's cache
        cached_func = cache(self._func)
        getattr(owner, _CHILD_CACHE)[self.id] = cached_func
        
        return cached_func

    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        owner = args[0]  # Assumes first arg is caller (i.e. called as a bound method)
        cached_func = self.get_cached_func(owner)
        return cached_func(*args, **kwds)
