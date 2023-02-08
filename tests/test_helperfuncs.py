from enum import Enum
import pytest
from respread import Node, redirect


class TCases(Enum):
    valid = 0
    caught_exception = 1
    secondary_caught_exception = 2
    uncaught_exception = 3


class Parent(Node):
    
    def redirected(self, tcase: TCases):
        match tcase:
            case TCases.valid:
                return f'Parent.redirected with tcase {tcase}'
            case TCases.caught_exception:
                raise ValueError
            case TCases.secondary_caught_exception:
                raise IndexError
            case TCases.uncaught_exception:
                raise ZeroDivisionError
            
    def mirror(self, tcase: TCases):
        match tcase:
            case TCases.valid:
                return f'Parent.mirror with tcase {tcase}'
            case TCases.caught_exception:
                raise ValueError
            case TCases.secondary_caught_exception:
                raise IndexError
            case TCases.uncaught_exception:
                raise ZeroDivisionError


class Child(Node):
    
    @redirect(('root', 'redirected'), ValueError)
    def redirected_func(self, tcase: TCases):
        return f'Child.redirected_func with tcase {tcase}'
    
    @redirect(('root',), ValueError, append_name=True)
    def mirror(self, tcase: TCases):
        return f'Child.mirror with tcase {tcase}'
    
    @redirect(('root', 'redirected'), (ValueError, IndexError))
    def multi_exception(self, tcase: TCases):
        return f'Child.multi_exception with tcase {tcase}'
    
    @redirect(('root', 'non_existent_attr'), ValueError)
    def doesnt_exist(self, tcase: TCases):
        pass  # never reached

parent = Parent()
child = Child()
parent.add_child('child', child.set_parent(parent))


def test_redirected_func():
    assert child.redirected_func(TCases.valid) == 'Parent.redirected with tcase TCases.valid'
    assert child.redirected_func(TCases.caught_exception) == 'Child.redirected_func with tcase TCases.caught_exception'
    with pytest.raises(ZeroDivisionError):
        child.redirected_func(TCases.uncaught_exception)

def test_mirrored_func():
    assert child.mirror(TCases.valid) == 'Parent.mirror with tcase TCases.valid'
    assert child.mirror(TCases.caught_exception) == 'Child.mirror with tcase TCases.caught_exception'
    with pytest.raises(ZeroDivisionError):
        child.mirror(TCases.uncaught_exception)

def test_multi_exception():
    assert child.multi_exception(TCases.caught_exception) == 'Child.multi_exception with tcase TCases.caught_exception'
    assert child.multi_exception(TCases.secondary_caught_exception) == 'Child.multi_exception with tcase TCases.secondary_caught_exception'

def test_bad_path():
    with pytest.raises(ValueError):
        child.doesnt_exist(TCases.valid)
