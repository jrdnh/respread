from functools import _lru_cache_wrapper, cache
from types import MethodType, SimpleNamespace
import pytest

from respread.series import AbstractSeries, cached_series, is_series, IS_SERIES, series, _SERIES_CACHE


def empty():
    return


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


# ------------------------------
# is_series
def test_is_series_no_attr():
    obj = SimpleNamespace()
    assert not is_series(obj)

def test_is_series_no_attr_is_false():
    obj = SimpleNamespace()
    setattr(obj, IS_SERIES, False)
    assert not is_series(obj)

def test_is_series_no_attr_is_true():
    obj = SimpleNamespace()
    setattr(obj, IS_SERIES, True)
    assert is_series(obj)

# ------------------------------
# Abstract Series
def test_abstract_series_is_series():
    abs = AbstractSeries(empty)
    assert is_series(abs)

def test_abstract_series_init():
    abs = AbstractSeries(empty)
    assert abs._func == empty

def test_abstract_series_set_name():
    class EmptyClass():
        @AbstractSeries
        def wrapped_func():
            pass
    assert EmptyClass.wrapped_func.__name__ == 'wrapped_func'

def test_abstract_series_get():
    class EmptyClass():
        @AbstractSeries
        def wrapped_func():
            pass
    assert type(EmptyClass.wrapped_func) == AbstractSeries
    ec = EmptyClass()
    assert type(ec.wrapped_func) == MethodType

def test_abstract_series_call():
    class EmptyClass():
        @AbstractSeries
        def wrapped_func(*args, **kwds):
            return (args, kwds)
    ec = EmptyClass()
    assert ec.wrapped_func(1, two=2) == ((ec, 1), {'two': 2})

# ------------------------------
# series
def test_series(inputs_func, owner_with_cache):
    s = series(inputs_func)
    owner_with_cache.series = MethodType(s, owner_with_cache)
    assert owner_with_cache.series() == ((owner_with_cache,), {})
    assert not getattr(owner_with_cache, _SERIES_CACHE)  # cache should be empty, empty dict asserts to False

# ------------------------------
# cached_series
def test_cached_series_id():
    s = cached_series(inputs_func)
    assert s.id == hash((id(inputs_func), id(s)))

def test_cached_series_owner_with_empty_cache(inputs_func, owner_with_cache):
    s = cached_series(inputs_func)
    owner_with_cache.series = MethodType(s, owner_with_cache)
    assert owner_with_cache.series() == ((owner_with_cache,), {})  # response value
    cached_func = getattr(owner_with_cache, _SERIES_CACHE)[s.id]
    assert isinstance(cached_func, _lru_cache_wrapper)  # cached objected is an lru cache type
    assert cached_func.__wrapped__ == s._func  # the cached func is the correct func
    assert cached_func.cache_info() == (0, 1, None, 1)  # calling the attr actually calls the cached value
    owner_with_cache.series()
    assert cached_func.cache_info() == (1, 1, None, 1)  # calling the attr actually calls the cached value
    # test that replacing attribute caches correctly
    new_s = cached_series(inputs_func)
    owner_with_cache.series = MethodType(new_s, owner_with_cache)  # replace attr
    assert owner_with_cache.series() == ((owner_with_cache,), {})  # response value
    cached_func = getattr(owner_with_cache, _SERIES_CACHE)[new_s.id]
    assert isinstance(cached_func, _lru_cache_wrapper)  # cached objected is an lru cache type
    assert cached_func.__wrapped__ == new_s._func  # the cached func is the correct func
    assert cached_func.cache_info() == (0, 1, None, 1)  # calling the attr actually calls the cached value

def test_cached_series_with_existing_cache(inputs_func, owner_with_cache):
    s = cached_series(inputs_func)
    owner_with_cache.series = MethodType(s, owner_with_cache)
    cached_func = cache(s._func)
    getattr(owner_with_cache, _SERIES_CACHE)[s.id] = cached_func
    assert owner_with_cache.series() == ((owner_with_cache,), {})  # response value
    assert len(getattr(owner_with_cache, _SERIES_CACHE)) == 1
    owner_with_cache.series()
    assert cached_func.cache_info() == (1, 1, None, 1)  # calling the series calls the already cached func

def test_cached_series_owner_with_no_existing_cache_attr(inputs_func, owner_without_cache):
    s = cached_series(inputs_func)
    owner_without_cache.series = MethodType(s, owner_without_cache)
    owner_without_cache.series(None)
    assert hasattr(owner_without_cache, _SERIES_CACHE)
    assert getattr(owner_without_cache, _SERIES_CACHE)[s.id].__wrapped__ == s._func
