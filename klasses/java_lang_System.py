import time
from classconstants import void, null

class OutPrintStream(NativeClassInstance):
    pass

def registerNatives(klass, vm, method, frame):
    PrintStream = vm.load_class('java/io/PrintStream')
    #out.natives[Class.method_name(

    return void

def nanoTime(klass, vm, method, frame):
    return int(time.time()*1e9)

def currentTimeMillis(klass, vm, method, frame):
    return 0

def identityHashCode(klass, vm, method, frame):
    obj = frame.get_local(0)
    if obj is null:
        return 0
    return hash(obj)
