from types import MethodType, SimpleNamespace
from typing import Callable
import pytest

from respread import (cached_series, 
                      DynamicSeriesGroup, 
                      is_series, 
                      series, 
                      SeriesGroup)
from respread.seriesgroup import DynamicSeriesGroupMeta, SeriesGroupIterator
from respread.series import _SERIES_CACHE, IS_SERIES


# ----------------------------
# Fixtures
@pytest.fixture
def empty_sg() -> SeriesGroup:
    return SeriesGroup()

@pytest.fixture
def nested_sg() -> SeriesGroup:
    class GroupA(SeriesGroup):
        @cached_series
        def childa_func(self, num):
            return f'childa_func: {num}'
    
    class GroupB(SeriesGroup):
        def __init__(self, childa: GroupA, parent: SeriesGroup | None = None) -> None:
            super().__init__(parent, children={'childa': childa})
        @cached_series
        def childb_func(self, num):
            return f'childb_func: {num}'
    
    return GroupB(GroupA())
    

# ----------------------------
# Tests: is_series
def test_is_series(empty_sg):
    assert is_series(empty_sg)

def test_empty_init(empty_sg: SeriesGroup):
    assert empty_sg.parent is None
    assert empty_sg.children == tuple()
    assert getattr(empty_sg, _SERIES_CACHE) == {}

# ----------------------------
# Tests: SeriesGroup
def test_init_parent():
    parent = SimpleNamespace()
    sg = SeriesGroup(parent=parent)
    assert sg.parent is parent

def test_init_children():
    # children added in init will have their parent set to the initializing 
    # SeriesGroup (if child has a `parent` attribute)
    non_sg_child = SimpleNamespace()
    sg_child = SeriesGroup()
    sg = SeriesGroup(children={'non_sg_child': non_sg_child, 'sg_child': sg_child})
    assert sg.children == ('non_sg_child', 'sg_child')
    assert sg.non_sg_child is non_sg_child
    assert sg.sg_child is sg_child
    assert sg_child.parent is sg

def test_add_series_to_children():
    series_defined_outside_class = SimpleNamespace()
    setattr(series_defined_outside_class, IS_SERIES, True)
    
    class SuperSG(SeriesGroup):
        @series
        def super_series(self):
            pass
        @cached_series
        def super_cached_series(self):
            pass
        @series
        def override(self):
            return 'super'
    
    class SubSeries(SuperSG):
        def non_series_func(self):
            pass
        @series
        def sub_series(self):
            pass
        @series
        def override(self):
            return 'sub'
        series_func_defined_outside_class = series_defined_outside_class
    
    init_series = SeriesGroup()
    sub_sg = SubSeries(children={'init_series': init_series})
    
    assert sub_sg.children == ('init_series', 'super_series', 'super_cached_series', 'override', 'sub_series', 'series_func_defined_outside_class')
    assert sub_sg.override() == 'sub'

def test_set_parent(empty_sg: SeriesGroup):
    parent = SimpleNamespace()
    ret_value = empty_sg.set_parent(parent)
    assert empty_sg.parent is parent
    assert ret_value is empty_sg

def test_children_property():
    # SeriesGroup object must have an attribute matching each 
    # value in the new children list or will raise a ValueError
    child_1 = SeriesGroup()
    child_2 = SeriesGroup()
    parent = SeriesGroup(children={'child_1': child_1, 'child_2': child_2})
    assert parent.children == ('child_1', 'child_2')
    parent.children = tuple()
    assert parent.children == tuple()
    parent.children = ('child_1',)
    assert parent.children == ('child_1',)
    with pytest.raises(ValueError, match=f"Cannot find attribute 'xyz' for object {parent}"):
        parent.children = ('child_2', 'xyz')

def test_add_child(empty_sg: SeriesGroup):
    child = lambda self: None
    empty_sg.add_child('new_child', child)
    # add to empty
    assert empty_sg.children == ('new_child',)
    assert empty_sg.new_child is child
    # add at default end
    second_child = lambda self: self
    empty_sg.add_child('another_child', second_child)
    assert empty_sg.children == ('new_child', 'another_child')
    # new with index
    empty_sg.another_child is second_child
    third_child = lambda self: self
    empty_sg.add_child('yet_another_child', MethodType(third_child, empty_sg), index=1)
    assert empty_sg.children == ('new_child', 'yet_another_child', 'another_child')
    assert empty_sg.yet_another_child() is empty_sg
    # replace with no index, not series
    replacement = SimpleNamespace()
    empty_sg.add_child('yet_another_child', replacement)
    assert empty_sg.children == ('new_child', 'yet_another_child', 'another_child')
    assert empty_sg.yet_another_child is replacement
    # replace multiple with index
    second_replacement = SimpleNamespace()
    empty_sg.children = ['new_child', *empty_sg.children]
    empty_sg.add_child('new_child', second_replacement, index=1)
    assert empty_sg.children == ('yet_another_child', 'new_child', 'another_child')
    assert empty_sg.new_child is second_replacement

def test_setattr(empty_sg: SeriesGroup):
    # any values that are series should automatically be added to `children` other than if name is `parent`
    # try parent
    parent = SeriesGroup()
    empty_sg.parent = parent
    assert empty_sg.parent is parent
    # series attr (should be added to children, does not set parent)
    new_sg_child = SeriesGroup()
    empty_sg.new_sg_child = new_sg_child
    assert empty_sg.children == ('new_sg_child',)
    assert empty_sg.new_sg_child is new_sg_child
    assert new_sg_child.parent is None
    # replace series attr
    overriding_sg = SeriesGroup()
    empty_sg.new_sg_child = overriding_sg
    assert empty_sg.children == ('new_sg_child',)
    assert empty_sg.new_sg_child is overriding_sg
    # non-series attr
    non_series_attr = SimpleNamespace()
    empty_sg.non_series = non_series_attr
    assert empty_sg.children == ('new_sg_child',)
    assert empty_sg.non_series is non_series_attr

def test_delattr(empty_sg: SeriesGroup):
    # delete child
    empty_sg.add_child('new_child', SeriesGroup())
    del empty_sg.new_child
    assert not hasattr(empty_sg, 'new_child')
    assert empty_sg.children == tuple()
    # delete non-child
    empty_sg.non_child = SimpleNamespace()
    del empty_sg.non_child
    assert not hasattr(empty_sg, 'new_child')

def test_attr_above():
    
    class SuperParent(SeriesGroup):
        @series
        def funca(self):
            return 'superparent funca'
        @series
        def funcb(self):
            return 'superparent funcb'
    
    class Parent(SeriesGroup):
        @series
        def funca(self):
            return 'parent funca'
        @series
        def funcc(self):
            return 'parent funcc'
    class Child(SeriesGroup):
        @series
        def funca(self):
            return 'child funca'
        @series
        def funcd(self):
            return 'child funcd'
    
    with pytest.raises(ValueError, match=f'No attribute "xyz" above object'):
        Child().attr_above('xyz')
    child = Child(parent=Parent(parent=SuperParent()))
    with pytest.raises(ValueError, match=f'No attribute "funcd" above object'):
        child.attr_above('funcd')
    assert child.attr_above('funcc') == child.parent.funcc
    assert child.attr_above('funca') == child.parent.funca
    assert child.attr_above('funcb') == child.parent.parent.funcb

def test_call(nested_sg):
    assert nested_sg(4) == ('childa_func: 4', 'childb_func: 4')
    assert nested_sg.childa(4) == ('childa_func: 4',)
    nested_sg.add_child('an_int', 0)
    with pytest.raises(TypeError, match="'int' object is not callable"):
        nested_sg(4)

def test_items(nested_sg):
    assert nested_sg.items(4) == ((('childa', 'childa_func'), 'childa_func: 4'), (('childb_func',), 'childb_func: 4'))
    assert nested_sg.childa.items(4) == ((('childa_func',), 'childa_func: 4'),)

def test_names(nested_sg):
    assert nested_sg.names() == ('childa.childa_func', 'childb_func')
    assert nested_sg.names(sep='***') == ('childa***childa_func', 'childb_func')
    assert nested_sg.names(sep=1) == ('childa1childa_func', 'childb_func')
    assert nested_sg.childa.names() == ('childa_func',)

def tests_iter(nested_sg):
    iterator = nested_sg.__iter__() 
    assert next(iterator) == (('childa', 'childa_func'), nested_sg.childa.childa_func)
    assert next(iterator) == (('childb_func',), nested_sg.childb_func)
    with pytest.raises(StopIteration):
        assert next(iterator)

def test_cache_clear(nested_sg):
    nested_sg(4), nested_sg(4)  # call twice to register one hit and one miss
    nested_sg.cache_clear()
    assert not getattr(nested_sg, _SERIES_CACHE)  # empty dict equals False
    assert not getattr(nested_sg.childa, _SERIES_CACHE)
    nested_sg(4), nested_sg(4)
    nested_sg.childa.cache_clear(all_nodes=False)
    assert getattr(nested_sg, _SERIES_CACHE)
    assert not getattr(nested_sg.childa, _SERIES_CACHE)
    nested_sg(4), nested_sg(4)
    nested_sg.childa.cache_clear(all_nodes=True)
    assert not getattr(nested_sg, _SERIES_CACHE)
    assert not getattr(nested_sg.childa, _SERIES_CACHE)

def test_enter(nested_sg):
    nested_sg(4), nested_sg(4)  # call twice to register one hit and one miss
    res = nested_sg.__enter__()
    assert res is nested_sg
    assert not getattr(nested_sg, _SERIES_CACHE)
    assert not getattr(nested_sg.childa, _SERIES_CACHE)

def test_exit(nested_sg):
    nested_sg(4), nested_sg(4)  # call twice to register one hit and one miss
    nested_sg.__exit__(None, None, None)
    assert not getattr(nested_sg, _SERIES_CACHE)
    assert not getattr(nested_sg.childa, _SERIES_CACHE)
    assert nested_sg.__exit__(ValueError, None, None) == False

def test_series_group_iterator(nested_sg):
    # test SeriesGroup
    iterator = SeriesGroupIterator(nested_sg)
    assert iter(iterator) is iterator
    assert next(iterator) == (('childa', 'childa_func'), nested_sg.childa.childa_func)
    assert next(iterator) == (('childb_func',), nested_sg.childb_func)
    with pytest.raises(StopIteration):
        next(iterator)
    # empty SeriesGroup
    empty_iterator = SeriesGroupIterator(SeriesGroup())
    with pytest.raises(StopIteration):
        next(empty_iterator)

# ----------------------------
# Tests: DynamicSeriesGroupMeta
def test_dynamicseriesgroupmeta():
    class DSGMClass(metaclass=DynamicSeriesGroupMeta):
        my_string: str
        my_int: int
        my_func: Callable[[int, str], float]

    assert all(item in dir(DSGMClass) for item in ('my_string', 'my_int', 'my_func'))
    assert DSGMClass.__annotations__['my_string'] == str
    assert DSGMClass.__annotations__['my_int'] == int
    assert DSGMClass.__annotations__['my_func'] == Callable[[int, str], float]

# ----------------------------
# Tests: DynamicSeriesGroup
@pytest.fixture
def empty_dsg():
    return DynamicSeriesGroup()

@pytest.fixture
def dsg_subclass():
    class DSGSubclass(DynamicSeriesGroup):
        first_series: Callable
        second_series: Callable
        
        def get_derived_children(self):
            return tuple(self.__annotations__.keys())
        
        def series_factory(self, name: str) -> Callable:
            def series_func(self, period):
                return (self, name, period)
            return series_func
    
    return DSGSubclass()

def test_get_derived_children(empty_dsg: DynamicSeriesGroup, dsg_subclass: DynamicSeriesGroup):
    with pytest.raises(NotImplementedError):
        empty_dsg.get_derived_children()
    assert dsg_subclass.get_derived_children() == ('first_series', 'second_series')

def test_series_factory(empty_dsg, dsg_subclass):
    with pytest.raises(NotImplementedError):
        empty_dsg.series_factory('my_series_name')
    assert dsg_subclass.series_factory('first_series')(None, 'period_arg') == (None, 'first_series', 'period_arg')

def test_method_factory(empty_dsg, dsg_subclass):
    with pytest.raises(NotImplementedError):
        empty_dsg._method_factory('non_child_attr')
    assert isinstance(dsg_subclass._method_factory('first_series'), MethodType)
    assert dsg_subclass._method_factory('first_series')('period_arg') == (dsg_subclass, 'first_series', 'period_arg')

def test_getattr(dsg_subclass):
    assert dsg_subclass.__getattr__('items') == dsg_subclass.items
    fs = dsg_subclass.__getattr__('first_series')
    assert isinstance(fs, MethodType)
    assert fs('period_arg') == (dsg_subclass, 'first_series', 'period_arg')
    with pytest.raises(AttributeError):
        dsg_subclass.__getattr__('missing_attr')

def test_children(empty_dsg: DynamicSeriesGroup, dsg_subclass: DynamicSeriesGroup):
    with pytest.raises(NotImplementedError):
        empty_dsg.children
    assert dsg_subclass.children == ('first_series', 'second_series')
    dsg_subclass.add_child('null_child', None, index=0)
    assert dsg_subclass.children == ('first_series', 'second_series', 'null_child')
