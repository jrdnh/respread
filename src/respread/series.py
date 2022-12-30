# from abc import ABC
from functools import cache
from types import MethodType
from typing import Any, Callable, Generic, ParamSpec, TypeVar


_SERIES_CACHE = '_series_cache'
IS_SERIES = 'is_series'


# -----------------------------
# Helpers
def is_series(obj) -> bool:
    return getattr(obj, IS_SERIES, False)


# class SeriesType(ABC):
#     """Abstract base class for identifying types automatically treated as series."""
#     is_series = True # TODO: reference IS_SERIES in setting this

SeriesType = type('SeriesType', 
                       tuple(), 
                       {IS_SERIES: True, '__doc__': 'Mixin base class for identifying types automatically treated as series.'})


_P = ParamSpec('_P')
_T = TypeVar('_T')


class AbstractSeries(SeriesType):
    
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


# -----------------------------
# Concrete types of series

# series
class series(Generic[_P, _T], AbstractSeries):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__(func)


class cached_series(Generic[_P, _T], AbstractSeries):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__(func)
    
    @property
    def id(self):
        return hash((id(self._func), id(self)))
    
    def get_cached_func(self, owner):
        # check if the owner has a cache and the cache has a matching entry
        if ((owners_cache := getattr(owner, _SERIES_CACHE, False)) and 
            (cached_func := owners_cache.get(self.id, False))):
            return cached_func
        
        # if the owner does not have a cache, try creating one
        if not owners_cache:
            try:
                setattr(owner, _SERIES_CACHE, {})
            except:
                raise ValueError(f'Could not create a cache for {self} at object {owner}')
        
        # created new cached func and save to owner's cache
        cached_func = cache(self._func)
        getattr(owner, _SERIES_CACHE)[self.id] = cached_func
        
        return cached_func

    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        """Assumes first arg is caller (i.e. called as a bound method)."""
        owner = args[0]
        cached_func = self.get_cached_func(owner)
        return cached_func(*args, **kwds)
