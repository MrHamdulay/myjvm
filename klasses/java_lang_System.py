from classconstants import void, null

def registerNatives(klass, vm, method, frame):
    return void

def nanoTime(klass, vm, method, frame):
    return 0

def currentTimeMillis(klass, vm, method, frame):
    return 0

def identityHashCode(klass, vm, method, frame):
    obj = frame.get_local(0)
    if obj is null:
        return 0
    return hash(obj)
