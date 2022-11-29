from abc import ABC
from functools import cache
from typing import Callable, Generic, ParamSpec, TypeVar


_SERIES_CACHE = '_series_cache'


class SeriesType(ABC):
    """Abstract base class for identifying types automatically treated as 'Series'."""
    pass


_P = ParamSpec('_P')
_T = TypeVar('_T')


class series(Generic[_P, _T], SeriesType):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__()
        self._func = func
        self._id = id(self)

    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        return self._func(*args, **kwds)


class cached_series(Generic[_P, _T], SeriesType):
    
    def __init__(self, func: Callable[_P, _T]) -> None:
        super().__init__()
        self._func = func
        self._id = id(self)

    def __call__(self, *args: _P.args, **kwds: _P.kwargs) -> _T:
        """Assumes first arg is caller (i.e. called a method/always bound)."""
        owner = args[0]
        
        # check if the owner has a cache and the cache has a matching entry
        if ((owners_cache := getattr(owner, _SERIES_CACHE, False)) and 
            (cached_func := owners_cache.get(self._id, False))):
            return cached_func(*args, **kwds)
        
        # if the owner does not have a cache, try creating one
        if not cache:
            try:
                setattr(owner, _SERIES_CACHE, {})
            except:
                raise Warning(f'Could not create a cache for {self} at object {owner}')
        
        # created new cached func and save to owner's cache
        cached_func = cache(self._func)
        getattr(owner, _SERIES_CACHE)[self._id] = cached_func
        
        return cached_func(*args, **kwds)
