from functools import _lru_cache_wrapper, cache
from types import MethodType
import pytest

from respread.series import series, cached_series, _SERIES_CACHE


@pytest.fixture
def owner_with_cache():
    OwnerWCache = type('OwnerWCache', tuple(), {_SERIES_CACHE: {}})
    return OwnerWCache()


@pytest.fixture
def owner_without_cache():
    return type('OwnerWoCache', tuple(), {})


@pytest.fixture
def inputs_func():
    def f(*args, **kwds):
        return (args, kwds)
    return f


def test_series(inputs_func, owner_with_cache):
    s = series(inputs_func)
    owner_with_cache.series = MethodType(s, owner_with_cache)
    assert owner_with_cache.series() == ((owner_with_cache,), {})
    assert not getattr(owner_with_cache, _SERIES_CACHE)  # cache should be empty, empty dict asserts to False

def test_cached_series_owner_with_empty_cache(inputs_func, owner_with_cache):
    s = cached_series(inputs_func)
    owner_with_cache.series = MethodType(s, owner_with_cache)
    assert owner_with_cache.series() == ((owner_with_cache,), {})  # response value
    cached_func = getattr(owner_with_cache, _SERIES_CACHE)[s._id]
    assert isinstance(cached_func, _lru_cache_wrapper)  # cached objected is an lru cache type
    assert cached_func.__wrapped__ == s.func  # the cached func is the correct func
    assert cached_func.cache_info() == (0, 1, None, 1)  # calling the attr actually calls the cached value
    owner_with_cache.series()
    assert cached_func.cache_info() == (1, 1, None, 1)  # calling the attr actually calls the cached value
    # test that replacing attribute caches correctly
    new_s = cached_series(inputs_func)
    owner_with_cache.series = MethodType(new_s, owner_with_cache)  # replace attr
    assert owner_with_cache.series() == ((owner_with_cache,), {})  # response value
    cached_func = getattr(owner_with_cache, _SERIES_CACHE)[new_s._id]
    assert isinstance(cached_func, _lru_cache_wrapper)  # cached objected is an lru cache type
    assert cached_func.__wrapped__ == new_s.func  # the cached func is the correct func
    assert cached_func.cache_info() == (0, 1, None, 1)  # calling the attr actually calls the cached value

def test_caches_series_with_existing_cache(inputs_func, owner_with_cache):
    s = cached_series(inputs_func)
    owner_with_cache.series = MethodType(s, owner_with_cache)
    cached_func = cache(s.func)
    getattr(owner_with_cache, _SERIES_CACHE)[s._id] = cached_func
    assert owner_with_cache.series() == ((owner_with_cache,), {})  # response value
    assert len(getattr(owner_with_cache, _SERIES_CACHE)) == 1
    owner_with_cache.series()
    assert cached_func.cache_info() == (1, 1, None, 1)  # calling the series calls the already cached func
    