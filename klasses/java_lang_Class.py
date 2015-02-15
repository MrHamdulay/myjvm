from __future__ import absolute_import
from excep import ClassNotFoundException
from classconstants import void, null
from klass import ArrayInstance
from utils import make_string, to_python_string
import descriptor

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
            'modifiers': 1,#field.access_flags,
            'signature': make_string(vm, ''),
            'annotations': null,
        })
        fields.array[i] = f
    return fields

def getDeclaredConstructors0(klass, vm, method, frame):
    Constructor = vm.load_class('java/lang/reflect/Constructor')
    instance = frame.get_local(0)
    constructors = []
    for method_name, method in instance._klass.methods.iteritems():
        if not method_name.startswith('<init>'):
            continue
        parameters = [vm.load_class(x).java_instance for x in descriptor.parse_descriptor(method.descriptor)[0]]
        parameterTypes = ArrayInstance(vm.load_class('java/lang/Class'), len(parameters))
        parameterTypes.array = parameters
        constructor = Constructor.instantiate()
        constructor._values.update({
            'clazz': Constructor.java_instance,
            'modifiers': 1, #method.access_flags,
            'parameterTypes': parameterTypes,
            'checkedExceptions': null, # XXX not implemented
            'annotations': null, # XXX: not implemented
            'parameterAnnotations': null # XXX: not implemented
        })
        constructors.append(constructor)
    c = ArrayInstance(Constructor, len(constructors))
    c.array = constructors
    return c

def desiredAssertionStatus0(klass, vm, method, frame):
    return 0

def forName0(klass, vm, method, frame):
    classname = to_python_string(frame.get_local(0))
    try:
        return vm.load_class(classname.replace('.', '/')).java_instance
    except ClassNotFoundException:
        vm.throw_exception(frame, 'java/lang/ClassNotFoundException')
        return null

def isInterface(klass, vm, method, frame):
    java_instance = frame.get_local(0)
    klass = vm.load_class(java_instance._values['class_name'])
    return klass.is_interface

def getName0(klass, vm, method, frame):
    return make_string(vm, frame.get_local(0)._values['class_name'])

def isArray(klass, vm, method, frame):
    return frame.get_local(0)._values['class_name'][0] == '['

def getComponentType(klass, vm, method, frame):
    return vm.load_class(frame.get_local(0)._values['class_name'][1:]).java_instance

def isPrimitive(klass, vm, method, frame):
    klass = vm.load_class(frame.get_local(0)._values['class_name'])
    return klass.primitive

def getModifiers(klass, vm, method, frame):
    return 1 #XXX: not implemented
