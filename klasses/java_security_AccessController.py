from __future__ import absolute_import
from klass import Class

def doPrivileged(klass, vm, method, frame):
    action = frame.get_local(0)
    run_method_name = Class.method_name('run', '()Ljava/lang/Object;')
    method = action._klass.methods[run_method_name]
    # instance to call on
    result = vm.wrap_run_method(action, method)
    return result
