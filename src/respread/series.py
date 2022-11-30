from abc import ABC
from functools import cache, wraps


_SERIES_CACHE = '_series_cache'
IS_SERIES = 'is_series'


def is_series(obj) -> bool:
    return getattr(obj, IS_SERIES, False)


class SeriesType(ABC):
    """Abstract base class for identifying types automatically treated as series."""
    is_series = True # TODO: reference IS_SERIES in setting this


def series(func):
    setattr(func, IS_SERIES, True)
    return func


def cached_series(func):
    
    @wraps(func)
    def wrapper(self, *args, **kwds):
        # check if self has a cache and the cache has a matching entry
        if ((owners_cache := getattr(self, _SERIES_CACHE, False)) and 
            (cached_func := owners_cache.get(id(func), False))):
            return cached_func(self, *args, **kwds)
        
        # if self does not have a cache, try creating one
        if not cache:
            try:
                setattr(self, _SERIES_CACHE, {})
            except:
                raise Warning(f'Could not create a cache for {func} at object {self}')
        
        # created new cached func and save to selfs's cache
        cached_func = cache(func)
        getattr(self, _SERIES_CACHE)[id(func)] = cached_func
        
        return cached_func(self, *args, **kwds)
    
    setattr(wrapper, IS_SERIES, True)
    return wrapper
