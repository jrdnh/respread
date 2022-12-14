from types import MethodType, SimpleNamespace
import pytest

from respread import cached_series, is_series, series, SeriesGroup
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
# Tests
def test_is_series(empty_sg):
    assert is_series(empty_sg)

def test_empty_init(empty_sg: SeriesGroup):
    assert empty_sg.parent is None
    assert empty_sg.children == tuple()
    assert getattr(empty_sg, _SERIES_CACHE) == {}

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
    
    assert sub_sg.children == ('super_series', 'super_cached_series', 'override', 'sub_series', 
                               'series_func_defined_outside_class', 'init_series')
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
    assert nested_sg(4) == ('childb_func: 4', 'childa_func: 4')
    assert nested_sg.childa(4) == ('childa_func: 4',)
    nested_sg.add_child('an_int', 0)
    with pytest.raises(TypeError, match="'int' object is not callable"):
        nested_sg(4)

def test_items(nested_sg):
    assert nested_sg.items(4) == ((('childb_func',), 'childb_func: 4'), (('childa', 'childa_func'), 'childa_func: 4'))
    assert nested_sg.childa.items(4) == ((('childa_func',), 'childa_func: 4'),)

def test_names(nested_sg):
    assert nested_sg.names() == ('childb_func', 'childa.childa_func')
    assert nested_sg.names(sep='***') == ('childb_func', 'childa***childa_func')
    assert nested_sg.names(sep=1) == ('childb_func', 'childa1childa_func')
    assert nested_sg.childa.names() == ('childa_func',)

def tests_iter(nested_sg):
    iterator = nested_sg.__iter__() 
    assert next(iterator) == (('childb_func',), nested_sg.childb_func)
    assert next(iterator) == (('childa', 'childa_func'), nested_sg.childa.childa_func)
    with pytest.raises(StopIteration):
        assert next(iterator)

# update cached_series objects to propgate cache_info and cache_clear

