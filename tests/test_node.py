from types import MethodType, SimpleNamespace
from typing import Callable
import pytest

from respread import (cached_child, 
                      child, 
                      DynamicNode, 
                      is_component, 
                      Node)
from respread.node import DynamicNodeMeta, NodeIterator
from respread.child import _CHILD_CACHE, IS_COMPONENT


# ----------------------------
# Fixtures
@pytest.fixture
def empty_node() -> Node:
    return Node()

@pytest.fixture
def nested_node() -> Node:
    class GroupA(Node):
        @cached_child
        def childa_func(self, num):
            return f'childa_func: {num}'
    
    class GroupB(Node):
        def __init__(self, childa: GroupA, parent: Node | None = None) -> None:
            super().__init__(parent, children={'childa': childa})
            self.childa = childa.set_parent(self)
        @cached_child
        def childb_func(self, num):
            return f'childb_func: {num}'
    
    return GroupB(GroupA())
    

# ----------------------------
# Tests: is_component
def test_is_component(empty_node):
    assert is_component(empty_node)

def test_empty_init(empty_node: Node):
    assert empty_node.parent is None
    assert empty_node.children == tuple()
    assert getattr(empty_node, _CHILD_CACHE) == {}

# ----------------------------
# Tests: Node
def test_init_parent():
    parent = SimpleNamespace()
    node = Node(parent=parent)
    assert node.parent is parent

def test_init_children():
    non_node_child = SimpleNamespace()
    node_child = Node()
    node = Node(children={'non_node_child': non_node_child, 'node_child': node_child})
    assert node.children == ('non_node_child', 'node_child')
    assert node.non_node_child is non_node_child
    assert node.node_child is node_child

def test_add_child_to_children():
    child_defined_outside_class = SimpleNamespace()
    setattr(child_defined_outside_class, IS_COMPONENT, True)
    
    class SuperNode(Node):
        @child
        def super_child(self):
            pass
        @cached_child
        def super_cached_child(self):
            pass
        @child
        def override(self):
            return 'super'
    
    class SubChild(SuperNode):
        def non_child(self):
            pass
        @child
        def sub_child(self):
            pass
        @child
        def override(self):
            return 'sub'
        child_func_defined_outside_class = child_defined_outside_class
    
    init_child = Node()
    sub_node = SubChild(children={'init_child': init_child})
    
    assert sub_node.children == ('init_child', 'super_child', 'super_cached_child', 'override', 'sub_child', 'child_func_defined_outside_class')
    assert sub_node.override() == 'sub'

def test_set_parent(empty_node: Node):
    parent = SimpleNamespace()
    ret_value = empty_node.set_parent(parent)
    assert empty_node.parent is parent
    assert ret_value is empty_node

def test_children_property():
    # Node object must have an attribute matching each 
    # value in the new children list or will raise a ValueError
    child_1 = Node()
    child_2 = Node()
    parent = Node(children={'child_1': child_1, 'child_2': child_2})
    assert parent.children == ('child_1', 'child_2')
    parent.children = tuple()
    assert parent.children == tuple()
    parent.children = ('child_1',)
    assert parent.children == ('child_1',)
    with pytest.raises(ValueError, match=f"Cannot find attribute 'xyz' for object {parent}"):
        parent.children = ('child_2', 'xyz')

def test_add_child(empty_node: Node):
    child = lambda self: None
    empty_node.add_child('new_child', child)
    # add to empty
    assert empty_node.children == ('new_child',)
    assert empty_node.new_child is child
    # add at default end
    second_child = lambda self: self
    empty_node.add_child('another_child', second_child)
    assert empty_node.children == ('new_child', 'another_child')
    # new with index
    empty_node.another_child is second_child
    third_child = lambda self: self
    empty_node.add_child('yet_another_child', MethodType(third_child, empty_node), index=1)
    assert empty_node.children == ('new_child', 'yet_another_child', 'another_child')
    assert empty_node.yet_another_child() is empty_node
    # replace with no index, not child
    replacement = SimpleNamespace()
    empty_node.add_child('yet_another_child', replacement)
    assert empty_node.children == ('new_child', 'yet_another_child', 'another_child')
    assert empty_node.yet_another_child is replacement
    # replace multiple with index
    second_replacement = SimpleNamespace()
    empty_node.children = ['new_child', *empty_node.children]
    empty_node.add_child('new_child', second_replacement, index=1)
    assert empty_node.children == ('yet_another_child', 'new_child', 'another_child')
    assert empty_node.new_child is second_replacement

def test_setattr(empty_node: Node):
    # any values that are child should automatically be added to `children` other than if name is `parent`
    # try parent
    parent = Node()
    empty_node.parent = parent
    assert empty_node.parent is parent
    # child attr (should be added to children, does not set parent)
    new_node_child = Node()
    empty_node.new_node_child = new_node_child
    assert empty_node.children == ('new_node_child',)
    assert empty_node.new_node_child is new_node_child
    assert new_node_child.parent is None
    # replace child attr
    overriding_node = Node()
    empty_node.new_node_child = overriding_node
    assert empty_node.children == ('new_node_child',)
    assert empty_node.new_node_child is overriding_node
    # non-child attr
    non_child_attr = SimpleNamespace()
    empty_node.non_child = non_child_attr
    assert empty_node.children == ('new_node_child',)
    assert empty_node.non_child is non_child_attr

def test_delattr(empty_node: Node):
    # delete child
    empty_node.add_child('new_child', Node())
    del empty_node.new_child
    assert not hasattr(empty_node, 'new_child')
    assert empty_node.children == tuple()
    # delete non-child
    empty_node.non_child = SimpleNamespace()
    del empty_node.non_child
    assert not hasattr(empty_node, 'new_child')

def test_root():
    
    class Parent(Node):
        @child
        def funca(self):
            return 'parent funca'
        @child
        def funcc(self):
            return 'parent funcc'
    
    class Child(Node):
        @child
        def funca(self):
            return 'child funca'
        @child
        def funcd(self):
            return 'child funcd'
    
    parent = Parent()
    child_obj = Child(parent=parent)
    assert child_obj.root is parent
    assert parent.root is parent

def test_attr_above():
    
    class SuperParent(Node):
        @child
        def funca(self):
            return 'superparent funca'
        @child
        def funcb(self):
            return 'superparent funcb'
    
    class Parent(Node):
        @child
        def funca(self):
            return 'parent funca'
        @child
        def funcc(self):
            return 'parent funcc'
    
    class Child(Node):
        @child
        def funca(self):
            return 'child funca'
        @child
        def funcd(self):
            return 'child funcd'
    
    with pytest.raises(ValueError, match=f'No attribute "xyz" above object'):
        Child().attr_above('xyz')
    child_obj = Child(parent=Parent(parent=SuperParent()))
    with pytest.raises(ValueError, match=f'No attribute "funcd" above object'):
        child_obj.attr_above('funcd')
    assert child_obj.attr_above('funcc') == child_obj.parent.funcc
    assert child_obj.attr_above('funca') == child_obj.parent.funca
    assert child_obj.attr_above('funcb') == child_obj.parent.parent.funcb

def test_display(nested_node):
    assert nested_node.display(4) == (('childa.childa_func', 'childa_func: 4'), ('childb_func', 'childb_func: 4'))
    assert nested_node.childa.display(4) == (('childa_func', 'childa_func: 4'),)
    def error_func(self, num):
        raise ValueError
    nested_node.childa = MethodType(error_func, nested_node)
    assert nested_node.display(4) == (('childa', None), ('childb_func', 'childb_func: 4'))

def test_items(nested_node):
    assert nested_node.items(4) == ((('childa', 'childa_func'), 'childa_func: 4'), (('childb_func',), 'childb_func: 4'))
    assert nested_node.childa.items(4) == ((('childa_func',), 'childa_func: 4'),)

def test_names(nested_node):
    assert nested_node.names() == ('childa.childa_func', 'childb_func')
    assert nested_node.names(sep='***') == ('childa***childa_func', 'childb_func')
    assert nested_node.names(sep=1) == ('childa1childa_func', 'childb_func')
    assert nested_node.childa.names() == ('childa_func',)

def test_values(nested_node):
    assert nested_node.values(4) == ('childa_func: 4', 'childb_func: 4')
    assert nested_node.childa.values(4) == ('childa_func: 4',)
    nested_node.add_child('an_int', 0)
    with pytest.raises(TypeError, match="'int' object is not callable"):
        nested_node.values(4)

def tests_iter(nested_node):
    iterator = nested_node.__iter__() 
    assert next(iterator) == (('childa', 'childa_func'), nested_node.childa.childa_func)
    assert next(iterator) == (('childb_func',), nested_node.childb_func)
    with pytest.raises(StopIteration):
        assert next(iterator)

def test_cache_clear(nested_node):
    nested_node(4), nested_node(4)  # call twice to register one hit and one miss
    nested_node.cache_clear()
    assert not getattr(nested_node, _CHILD_CACHE)  # empty dict equals False
    assert not getattr(nested_node.childa, _CHILD_CACHE)
    nested_node(4), nested_node(4)
    nested_node.childa.cache_clear(all_nodes=False)
    assert getattr(nested_node, _CHILD_CACHE)
    assert not getattr(nested_node.childa, _CHILD_CACHE)
    nested_node(4), nested_node(4)
    nested_node.childa.cache_clear(all_nodes=True)
    assert not getattr(nested_node, _CHILD_CACHE)
    assert not getattr(nested_node.childa, _CHILD_CACHE)

def test_enter(nested_node):
    nested_node(4), nested_node(4)  # call twice to register one hit and one miss
    res = nested_node.__enter__()
    assert res is nested_node
    assert not getattr(nested_node, _CHILD_CACHE)
    assert not getattr(nested_node.childa, _CHILD_CACHE)

def test_exit(nested_node):
    nested_node(4), nested_node(4)  # call twice to register one hit and one miss
    nested_node.__exit__(None, None, None)
    assert not getattr(nested_node, _CHILD_CACHE)
    assert not getattr(nested_node.childa, _CHILD_CACHE)
    assert nested_node.__exit__(ValueError, None, None) == False

def test_child_group_iterator(nested_node):
    # test Node
    iterator = NodeIterator(nested_node)
    assert iter(iterator) is iterator
    assert next(iterator) == (('childa', 'childa_func'), nested_node.childa.childa_func)
    assert next(iterator) == (('childb_func',), nested_node.childb_func)
    with pytest.raises(StopIteration):
        next(iterator)
    # empty Node
    empty_iterator = NodeIterator(Node())
    with pytest.raises(StopIteration):
        next(empty_iterator)

# ----------------------------
# Tests: DynamicNodeMeta
def test_dynamicnodemeta():
    class DNMClass(metaclass=DynamicNodeMeta):
        my_string: str
        my_int: int
        my_func: Callable[[int, str], float]

    assert all(item in dir(DNMClass) for item in ('my_string', 'my_int', 'my_func'))
    assert DNMClass.__annotations__['my_string'] == str
    assert DNMClass.__annotations__['my_int'] == int
    assert DNMClass.__annotations__['my_func'] == Callable[[int, str], float]

# ----------------------------
# Tests: DynamicNode
@pytest.fixture
def empty_dynamicnode():
    return DynamicNode()

@pytest.fixture
def dynamicnode_subclass():
    class DNMSubclass(DynamicNode):
        first_child: Callable
        second_child: Callable
        
        def get_derived_children(self):
            return tuple(self.__annotations__.keys())
        
        def child_factory(self, name: str) -> Callable:
            def child_func(self, period):
                return (self, name, period)
            return child_func
    
    return DNMSubclass()

def test_dir(dynamicnode_subclass: DynamicNode):
    obj_dir = object.__dir__(dynamicnode_subclass)
    expected_dir = sorted((*obj_dir, *dynamicnode_subclass.__annotations__.keys()))
    assert dir(dynamicnode_subclass) == expected_dir

def test_get_derived_children(empty_dynamicnode: DynamicNode, dynamicnode_subclass: DynamicNode):
    with pytest.raises(NotImplementedError):
        empty_dynamicnode.get_derived_children()
    assert dynamicnode_subclass.get_derived_children() == ('first_child', 'second_child')

def test_child_factory(empty_dynamicnode, dynamicnode_subclass):
    with pytest.raises(NotImplementedError):
        empty_dynamicnode.child_factory('my_child_name')
    assert dynamicnode_subclass.child_factory('first_child')(None, 'period_arg') == (None, 'first_child', 'period_arg')

def test_method_factory(empty_dynamicnode, dynamicnode_subclass):
    with pytest.raises(NotImplementedError):
        empty_dynamicnode._method_factory('non_child_attr')
    assert isinstance(dynamicnode_subclass._method_factory('first_child'), MethodType)
    assert dynamicnode_subclass._method_factory('first_child')('period_arg') == (dynamicnode_subclass, 'first_child', 'period_arg')

def test_getattr(dynamicnode_subclass):
    assert dynamicnode_subclass.__getattr__('items') == dynamicnode_subclass.items
    fs = dynamicnode_subclass.__getattr__('first_child')
    assert isinstance(fs, MethodType)
    assert fs('period_arg') == (dynamicnode_subclass, 'first_child', 'period_arg')
    with pytest.raises(AttributeError):
        dynamicnode_subclass.__getattr__('missing_attr')

def test_children(empty_dynamicnode: DynamicNode, dynamicnode_subclass: DynamicNode):
    with pytest.raises(NotImplementedError):
        empty_dynamicnode.children
    assert dynamicnode_subclass.children == ('first_child', 'second_child')
    dynamicnode_subclass.add_child('null_child', None, index=0)
    assert dynamicnode_subclass.children == ('first_child', 'second_child', 'null_child')
