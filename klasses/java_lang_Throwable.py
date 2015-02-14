from __future__ import absolute_import
from classconstants import void, null

def fillInStackTrace(klass, vm, method, frame):
    exception = frame.get_local(0)
    message = 'Exception thrown at:\n'
    for frame in vm.frame_stack[1::]:
        if not frame.klass:
            continue
        message += '%s.%s\n' % (frame.klass.name, frame.method.name)
        message += frame.pretty_code(vm)
    exception.stacktrace = message

    return frame.get_local(0)
