from __future__ import absolute_import
import time
from classconstants import void, null
from klass import Class, ArrayInstance
from utils import make_string

def arraycopy(klass, vm, method, frame):
    src = frame.get_local(0)
    srcPos = frame.get_local(1)
    dest = frame.get_local(2)
    destPos = frame.get_local(3)
    length = frame.get_local(4)
    if src is null or dest is null:
        vm.throw_exception(frame, 'java/lang/NullPointerException')
        return
    assert isinstance(src, ArrayInstance)
    assert isinstance(dest, ArrayInstance)
    for i in xrange(length):
        dest.array[destPos+i] = src.array[srcPos+i]
    return void

def registerNatives(klass, vm, method, frame):
    Properties = vm.load_class('java/util/Properties')
    @Properties.override_native_method('getProperty')
    def getProperty(klass, vm, method, frame):
        prop = frame.get_local(1)
        prop = ''.join(map(chr, prop._values['value'].array))
        if prop == 'sun.reflect.noCaches':
            return make_string(vm, 'false')
        elif prop == 'file.encoding':
            return make_string(vm, 'utf-8')
        elif prop in ('java.security.debug', 'java.security.auth.debug'):
            return make_string(vm, 'false')
        raise Exception('unknown property %s'  % prop)

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
    vm.wrap_run_method(system_out, method, system_out_stream)
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
