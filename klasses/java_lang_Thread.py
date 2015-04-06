from __future__ import absolute_import
from classconstants import void, null
from frame import Frame

global_thread = None
def initGlobalThread(vm, frame):
    global global_thread
    if global_thread is not None:
        return global_thread
    ThreadGroup = vm.load_class('java/lang/ThreadGroup')
    Thread = vm.load_class('java/lang/Thread')
    global_thread_group = ThreadGroup.instantiate()
    global_thread_group._values['name'] = 'main thread group'
    global_thread = Thread.instantiate()
    global_thread._values['name'] = 'main thread'
    global_thread._values['group'] = global_thread_group
    global_thread._values['priority'] = 1

    vm.wrap_run_method(global_thread_group, ThreadGroup.methods['add__(Ljava/lang/Thread;)V'], global_thread)
    return global_thread

def registerNatives(klass, vm, method, frame):
    klass.field_values['threadInitNumber'] = 0
    initGlobalThread(vm, frame)
    return void

def currentThread(klass, vm, method, frame):
    return initGlobalThread(vm, frame)

def setPriority0(klass, vm, method, frame):
    return void
