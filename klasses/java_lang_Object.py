from __future__ import absolute_import
from classconstants import void

def registerNatives(klass, vm, method, frame):
    return void

def hashCode(klass, vm, method, frame):
    return id(frame.get_local(0))
