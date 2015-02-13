import time
from classconstants import void, null
from klass import Class
from util import make_string


def registerNatives(klass, vm, method, frame):
    Properties = vm.load_class('java/util/Properties')
    @Properties.override_native_method('getProperty')
    def getProperty(klass, vm, method, frame):
        prop = frame.get_local(1)
        prop = ''.join(map(chr, prop._values['value']))
        if prop == 'sun.reflect.noCaches':
            return make_string(vm, 'false')

    @Properties.override_native_method('setProperty')
    def setProperty(klass, vm, method, frame):
        prop = frame.get_local(1)
        print 'setting property!', prop
        raise Exception



    OutputStream = vm.load_class('java/io/OutputStream')
    PrintOutputStream = Class('java/io/PrintOutputStream', super_class=OutputStream)
    @PrintOutputStream.override_native_method('write')
    def write(*args):
        print 'write', args

    PrintStream = vm.load_class('java/io/PrintStream')
    system_out = PrintStream.instantiate()
    system_out_stream = PrintOutputStream.instantiate()

    vm.stack.push(system_out)
    vm.stack.push(system_out_stream)
    klass.field_overrides['out'] = system_out
    klass.field_overrides['security'] = null
    klass.field_overrides['props'] = Properties.instantiate()

    print PrintStream.get_method('<init>', '(Ljava/io/OutputStream;)V')
    klass, method = PrintStream.get_method('<init>', '(Ljava/io/OutputStream;)V')
    vm.run_method(klass, method)
    vm.run_bytecode()
    raise Exception
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
