from classconstants import void, null

def registerNatives(klass, vm, method, frame):
    return void

def getPrimitiveClass(klass, vm, method, frame):
    klass_name = frame.get_local(0)
    assert klass_name._klass_name == 'java/lang/String'
    klass_name = ''.join(map(chr, klass_name._values['value']))
    return vm.load_class(klass_name)

def getClassLoader0(klass, vm, method, frame):
    return null

def desiredAssertionStatus0(klass, vm, method, frame):
    return 0
