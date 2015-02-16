from __future__ import absolute_import
from classconstants import void, null
from frame import Frame

global_thread = None
def initGlobalThread(vm, frame):
    global global_thread
    if global_thread is not None:
        return global_thread
    Thread = vm.load_class('java/lang/Thread')
    global_thread = Thread.instantiate()
    vm.wrap_run_method(global_thread, Thread.methods['<init>__()V'])
    return global_thread

def registerNatives(klass, vm, method, frame):
    klass.field_values['threadInitNumber'] = 0
    return void

def currentThread(klass, vm, method, frame):
    return initGlobalThread(vm, frame)
