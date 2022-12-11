# from abc import ABC
from functools import cache
from types import MethodType
from typing import Callable, Generic, ParamSpec, TypeVar


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


# -----------------------------
# Concrete types of series
_P = ParamSpec('_P')
_T = TypeVar('_T')


class series(Generic[_P, _T], SeriesType):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__()
        self._func = func
    
    def __set_name__(self, owner, name: str):
        self.__name__ = name        
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return MethodType(self, obj)

    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        return self._func(*args, **kwds)


class cached_series(Generic[_P, _T], SeriesType):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__()
        self._func = func
        self._id = id(self)
    
    def __set_name__(self, owner, name: str):
        self.__name__ = name
    
    @property
    def id(self):
        return hash((self._func, self._id))

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return MethodType(self, obj)

    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        """Assumes first arg is caller (i.e. called as a bound method)."""
        owner = args[0]
        
        # check if the owner has a cache and the cache has a matching entry
        if ((owners_cache := getattr(owner, _SERIES_CACHE, False)) and 
            (cached_func := owners_cache.get(self.id, False))):
            return cached_func(*args, **kwds)
        
        # if the owner does not have a cache, try creating one
        if not cache:
            try:
                setattr(owner, _SERIES_CACHE, {})
            except:
                raise Warning(f'Could not create a cache for {self} at object {owner}')
        
        # created new cached func and save to owner's cache
        cached_func = cache(self._func)
        getattr(owner, _SERIES_CACHE)[self.id] = cached_func
        
        return cached_func(*args, **kwds)
