from classconstants import void

def registerNatives(klass, vm, method, frame):
    return void

def getPrimitiveClass(klass, vm, method, frame):
    klass_name = frame.get_local(0)
    return vm.load_class(klass_name)
