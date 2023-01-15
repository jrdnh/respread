from functools import _lru_cache_wrapper, cache
from types import MethodType, SimpleNamespace
import pytest

from respread.child import cached_child, child, is_component, IS_COMPONENT, _CHILD_CACHE


def empty():
    return

@pytest.fixture
def child_types():
    """Return set of all child types."""
    return {child, cached_child}


@pytest.fixture
def owner_with_cache():
    OwnerWCache = type('OwnerWCache', tuple(), {_CHILD_CACHE: {}})
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
# is_component
def test_is_component_no_attr():
    obj = SimpleNamespace()
    assert not is_component(obj)

def test_is_component_no_attr_is_false():
    obj = SimpleNamespace()
    setattr(obj, IS_COMPONENT, False)
    assert not is_component(obj)

def test_is_component_no_attr_is_true():
    obj = SimpleNamespace()
    setattr(obj, IS_COMPONENT, True)
    assert is_component(obj)

# ------------------------------
# Common elements
def test_child_is_component(child_types):
    child_objs = (child_(empty) for child_ in child_types)
    for child_obj in child_objs:
        assert is_component(child_obj)

def test_child_init(child_types):
    child_objs = (child_(empty) for child_ in child_types)
    for child_obj in child_objs:
        assert child_obj._func == empty

def test_abstract_child_set_name(child_types):
    for child_type in child_types:
        class EmptyClass():
            @child_type
            def wrapped_func():
                pass
        assert EmptyClass.wrapped_func.__name__ == 'wrapped_func'

def test_child_get(child_types):
    for child_type in child_types:
        class EmptyClass():
            @child_type
            def wrapped_func():
                pass
        assert type(EmptyClass.wrapped_func) == child_type
        ec = EmptyClass()
        assert type(ec.wrapped_func) == MethodType

def test_child_call(child_types):
    for child_type in child_types:
        class EmptyClass():
            @child_type
            def wrapped_func(*args, **kwds):
                return (args, kwds)
        ec = EmptyClass()
        assert ec.wrapped_func(1, two=2) == ((ec, 1), {'two': 2})

# ------------------------------
# child
def test_child(inputs_func, owner_with_cache):
    c = child(inputs_func)
    owner_with_cache.child = MethodType(c, owner_with_cache)
    assert owner_with_cache.child() == ((owner_with_cache,), {})
    assert not getattr(owner_with_cache, _CHILD_CACHE)  # cache should be empty, empty dict asserts to False

# ------------------------------
# cached_child
def test_cached_child_id():
    c = cached_child(inputs_func)
    assert c.id == hash((id(inputs_func), id(c)))

def test_get_cached_func_with_immutable_owner(inputs_func):
    owner = tuple()
    cs = cached_child(inputs_func)
    with pytest.raises(ValueError):
        cs.get_cached_func(owner)

def test_cached_child_owner_with_empty_cache(inputs_func, owner_with_cache):
    c = cached_child(inputs_func)
    owner_with_cache.child = MethodType(c, owner_with_cache)
    assert owner_with_cache.child() == ((owner_with_cache,), {})  # response value
    cached_func = getattr(owner_with_cache, _CHILD_CACHE)[c.id]
    assert isinstance(cached_func, _lru_cache_wrapper)  # cached objected is an lru cache type
    assert cached_func.__wrapped__ == c._func  # the cached func is the correct func
    assert cached_func.cache_info() == (0, 1, None, 1)  # calling the attr actually calls the cached value
    owner_with_cache.child()
    assert cached_func.cache_info() == (1, 1, None, 1)  # calling the attr actually calls the cached value
    # test that replacing attribute caches correctly
    new_c = cached_child(inputs_func)
    owner_with_cache.child = MethodType(new_c, owner_with_cache)  # replace attr
    assert owner_with_cache.child() == ((owner_with_cache,), {})  # response value
    cached_func = getattr(owner_with_cache, _CHILD_CACHE)[new_c.id]
    assert isinstance(cached_func, _lru_cache_wrapper)  # cached objected is an lru cache type
    assert cached_func.__wrapped__ == new_c._func  # the cached func is the correct func
    assert cached_func.cache_info() == (0, 1, None, 1)  # calling the attr actually calls the cached value

def test_cached_child_with_existing_cache(inputs_func, owner_with_cache):
    c = cached_child(inputs_func)
    owner_with_cache.child = MethodType(c, owner_with_cache)
    cached_func = cache(c._func)
    getattr(owner_with_cache, _CHILD_CACHE)[c.id] = cached_func
    assert owner_with_cache.child() == ((owner_with_cache,), {})  # response value
    assert len(getattr(owner_with_cache, _CHILD_CACHE)) == 1
    owner_with_cache.child()
    assert cached_func.cache_info() == (1, 1, None, 1)  # calling the child calls the already cached func

def test_cached_child_owner_with_no_existing_cache_attr(inputs_func, owner_without_cache):
    c = cached_child(inputs_func)
    owner_without_cache.child = MethodType(c, owner_without_cache)
    owner_without_cache.child(None)
    assert hasattr(owner_without_cache, _CHILD_CACHE)
    assert getattr(owner_without_cache, _CHILD_CACHE)[c.id].__wrapped__ == c._func
