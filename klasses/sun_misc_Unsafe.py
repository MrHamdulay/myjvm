from __future__ import absolute_import
from classconstants import void, null

def arrayBaseOffset(klass, vm, method, frame):
    return 1

def arrayIndexScale(klass, vm, method, frame):
    return 1

def addressSize(klass, vm, method, frame):
    return 8

def compareAndSwapObject(klass, vm, method, frame):
    o = frame.get_local(1)
    offset = frame.get_local(2)
    expected = frame.get_local(3)
    x = frame.get_local(4)
    print 'object, offset, expected, exchange'
    print o, offset, expected, x
    if o.array[offset] == expected:
        o.array[offset] = x
        return 1
    return 0
