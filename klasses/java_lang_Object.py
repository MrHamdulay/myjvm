from __future__ import absolute_import
from classconstants import void
from copy import copy
from klass import ArrayInstance

def registerNatives(klass, vm, method, frame):
    return void

def hashCode(klass, vm, method, frame):
    return id(frame.get_local(0))

def getClass(klass, vm, method, frame):
    return frame.get_local(0)._klass.java_instance

def clone(klass, vm, method, frame):
    instance = copy(frame.get_local(0))
    print 'i', instance, frame.get_local(0)
    if isinstance(instance, ArrayInstance):
        for i, v in enumerate(instance.array):
            if isinstance(v, ClassInstance):
                instance.array[i] = vm.wrap_run_method(v, v.methods['clone__Ljava/lang/Object;'])
    else:
        newValues = {}
        for k, v in instance._values.iteritems():
            newValues[k]= v
            if isinstance(v, ClassInstance):
                newValues[k] = vm.wrap_run_method(v, v.methods['clone__Ljava/lang/Object;'])
        instance._values = newValues
    return instance
