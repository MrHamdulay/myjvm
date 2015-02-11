import logging

from utils import get_attribute
from constantpool import ConstantPool
from classtypes import CodeAttribute, Method
from classconstants import ACC_STATIC, ACC_NATIVE, ACC_INTERFACE, void, null
from descriptor import parse_descriptor

class NoSuchMethodException(Exception):
    pass

EMPTY_METHOD = Method(ACC_STATIC, '', '()V', [CodeAttribute(0, 0, [], [], [])], '', '')

class Class(object):
    def __init__(self,
            name=None,
            super_class=None,
            vm=None):
        self._klass = None
        self.name = name if name else self.__class__.__name__
        self.major_version, self.minor_version = -1, -1
        self.constant_pool = ConstantPool(0)
        self.access_flags = 0
        self.super_class = super_class
        self.interfaces = []
        self.fields = {}
        self.field_values = {}
        self.field_overrides = {}
        self.methods = {}
        self.attributes = []

    @property
    def is_array(self):
        return self.name[0] == '['


    def get_method(self, method_name, type_signature):
        built_method_name = Class.method_name(method_name, type_signature)
        if built_method_name in self.methods:
            return self, self.methods[built_method_name]

        # lookup in super class
        if '<clinit>' != method_name and self.super_class:
            try:
                return self.super_class.get_method(
                        method_name, type_signature)
            except NoSuchMethodException:
                pass

        # TODO: implement lookup for default methods in interfaces
        raise NoSuchMethodException('No such method %s.%s (%s)' % (
            self.name, method_name, type_signature) )

    def get_field(self, field_name):
        klass = self
        while field_name not in klass.fields:
            klass = klass.super_class
        return klass.fields[field_name]


    @property
    def is_interface(self):
        return self.access_flags & ACC_INTERFACE

    def implements(self, interface):
        if self is interface:
            return True
        for interf in self.interfaces:
            if interf.implements(interface):
                return True
        return False

    def is_subclass(self, instance):
        if isinstance(instance, Class):
            return self.name in ('java/lang/Class', 'java/lang/Object')
        else:
            klass = instance._klass
        while klass != self and klass != klass.super_class:
            print klass
            klass = klass.super_class
        print klass
        return klass == self

    def instantiate(self, size=None):
        if self.is_array:
            assert size is not None
            return ArrayClass(self, size)
        return ClassInstance(self.name, self)

    @staticmethod
    def fetch_native_method(class_name, method):
        assert method.access_flags & ACC_NATIVE
        assert not hasattr(method, 'code')
        try:
            if class_name not in classes_with_natives and \
                    method.name == 'registerNatives':
                native_method = (lambda *args: void)
            else:
                module = classes_with_natives[class_name]
                if method.name == 'registerNatives' and \
                        not 'registerNatives' in module.__dict__:
                    native_method = (lambda *args: void)
                else:
                    native_method = getattr(module, method.name)
        except (KeyError, AttributeError):
            raise Exception('Missing method %s on class %s' % (
                method.name, class_name))
        method.attributes.append(CodeAttribute(100, 100, [], [], []))
        return native_method

    def run_method(self, vm, method, method_descriptor):
        print self, method
        native_method = None
        # handle native methods
        if (method.access_flags & ACC_NATIVE) != 0:
            native_method = Class.fetch_native_method(self.name, method)

        code = get_attribute(method, 'Code')

        # may contain an instance argument (not STATIC
        is_static = method.access_flags & ACC_STATIC != 0
        num_args = len(method.parameters) + (0 if is_static else 1)
        arguments = [vm.frame_stack[-1].pop() for i in xrange(num_args)][::-1]
        if not is_static:
            #print arguments
            assert arguments[0] is not null, '%s is null' % str(arguments[0])
            instance = arguments[0]
        print 'adding method %s.%s to stack' % (self.name, method.name)
        frame = Frame(
                parameters=arguments,
                max_stack=code.max_stack,
                max_locals=code.max_locals,
                code=code,
                method=method,
                native_method=native_method,
                klass=self)

        vm.frame_stack.append(frame)

    def print_(self):
        print self.constant_pool
        print self.interfaces
        print self.fields
        print self.methods
        print self.attributes

    def __repr__(self):
        return '<Class %s%s> ' % (self.name, ' array' if self.is_array else '')

    @staticmethod
    def method_name(*args):
        if isinstance(args[0], Method):
            return '%s__%s' % (args[0].name, args[0].descriptor)
        elif len(args) == 2:
            return '%s__%s' % args
        raise Exception

    def override_native_method(self, f):
        print self.methods

class NativeClass(Class):
    def get_method(self, method_name, type_signature):
        if method_name in ('<init>', '<clinit>'):
            return self, Method(ACC_STATIC, method_name, type_signature, [], '', '')
        if method_name in self.methods:
            return self, self.methods[method_name]
        raise NoSuchMethodException('No such method %s.%s (%s)' % (self, method_name, type_signature) )

    def run_method(self, vm, method, method_descriptor):
        args = []
        if (method.access_flags & ACC_STATIC ) == 0:
            # method is not static so load instance
            args.append(vm.stack[-1].pop())
            if args[-1] == null:
                raise Exception('nullpointerexception')

        # parse argument list and return type
        method.parameters, method.return_type = parse_descriptor(method_descriptor)
        # read arguments into stack
        for arg_type in method.parameters:
            arg = vm.stack[-1].pop()
            args.append(arg)

        if method.name in ('<init>', '<clinit>'):
            return void
        return_value = getattr(self, method.name, None)(*args)
        if method.return_type == 'V':
            return void
        return return_value

class ClassInstance(object):
    _klass = None
    _klass_name = None
    _values = None

    def __init__(self, klass_name, klass):
        assert isinstance(klass, Class)
        assert klass_name == klass.name
        self._values = {}
        self._klass = klass
        self._klass_name = klass_name
        self.natives = {}

    def __repr__(self):
        if self._klass_name == 'java/lang/String':
            return '<String "%s">' % (''.join(chr(x)
                for x in self._values['value']))
        return '<Instance of "%s">' % (
            self._klass_name)
        return '<Instance of "%s" values:%s>' % (
            self._klass_name, self._values)

class ArrayClass(ClassInstance):
    _klass = None

    def __init__(self, klass, size):
        assert isinstance(klass, Class)
        self._klass = klass
        self._klass_name = klass.name
        self.array = [null] * size

    def __repr__(self):
        return '<Array %s size=%d> ' % (self._klass.name, len(self.array))

    @property
    def size(self):
        return len(self.array)

from frame import Frame
from klasses import classes_with_natives
