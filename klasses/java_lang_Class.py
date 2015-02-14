from __future__ import absolute_import
from excep import ClassNotFoundException
from classconstants import void, null
from klass import ArrayInstance
from utils import make_string, to_python_string

def registerNatives(klass, vm, method, frame):
    return void

def getPrimitiveClass(klass, vm, method, frame):
    klass_name = frame.get_local(0)
    assert klass_name._klass_name == 'java/lang/String'
    klass_name = ''.join(map(chr, klass_name._values['value'].array))
    return vm.load_class(klass_name).java_instance

def getClassLoader0(klass, vm, method, frame):
    return null

def getDeclaredFields0(klass, vm, method, frame):
    original_class = vm.load_class(frame.get_local(0)._values['class_name'])
    isPublic = frame.get_local(1) == 1
    Field = vm.load_class('java/lang/reflect/Field')
    fields = ArrayInstance(Field, len(original_class.fields.keys()))
    for i, field in enumerate(original_class.fields.itervalues()):
        f = Field.instantiate()
        f._values.update({
            'clazz': original_class.java_instance,
            'name': field.name,
            'type': vm.load_class(field.descriptor).java_instance,
            'modifiers': field.access_flags,
            'signature': make_string(vm, ''),
            'annotations': null,
        })
        fields.array[i] = f
    return fields

def desiredAssertionStatus0(klass, vm, method, frame):
    return 0

def forName0(klass, vm, method, frame):
    classname = to_python_string(frame.get_local(0))
    try:
        return vm.load_class(classname).java_instance
    except ClassNotFoundException:
        vm.throw_exception(frame, 'java/lang/ClassNotFoundException')
        return null
