import logging

from utils import get_attribute
from constantpool import ConstantPool
from classtypes import CodeAttribute, Method
from classconstants import ACC_STATIC, ACC_NATIVE, void
from frame import Frame
from descriptor import parse_descriptor
from klasses import classes_with_natives

class NoSuchMethodException(Exception):
    pass

EMPTY_METHOD = Method(ACC_STATIC, '', '()V', [CodeAttribute(0, 0, [], [], [])])

class Class(object):
    def __init__(self, name=None):
        self.name = name if name else self.__class__.__name__
        self.major_version, self.minor_version = -1, -1
        self.constant_pool = ConstantPool(0)
        self.access_flags = 0
        self.this_class = None
        self.super_class = None
        self.interfaces = []
        self.fields = {}
        self.field_values = {}
        self.methods = {}
        self.attributes = []

    def get_method(self, method_name, type_signature):
        built_method_name = Class.method_name(method_name, type_signature)
        if built_method_name in self.methods:
            return self.methods[built_method_name]
        raise NoSuchMethodException('No such method %s (%s)' % (method_name, type_signature) )

    def is_subclass(self, instance):
        klass = instance._klass
        while klass != self and klass != klass.super_class:
            klass = klass.super_class
        return klass == self

    def instantiate(self):
        return ClassInstance(self.method_name, self)

    @staticmethod
    def fetch_native_method(class_name, method):
        assert method.access_flags & ACC_NATIVE
        assert not hasattr(method, 'code')
        try:
            native_method = getattr(classes_with_natives[class_name], method.name)
        except (KeyError, AttributeError):
            raise Exception('Missing method %s on class %s' % (method.name, class_name))
        method.attributes.append(CodeAttribute(100, 100, [], [], []))
        return native_method

    def run_method(self, vm, method, method_descriptor):
        native_method = None
        # handle native methods
        if (method.access_flags & ACC_NATIVE) != 0:
            native_method = Class.fetch_native_method(self.name, method)

        code = get_attribute(method, 'Code')


        method_arguments, method_return_type = parse_descriptor(method.descriptor)
        # may contain an instance argument (not STATIC
        num_args = len(method_arguments) + (1 if (method.access_flags & ACC_STATIC == 0) else 0)
        print self.name, method.name, 'not static' if (method.access_flags & ACC_STATIC == 0) else 'static'
        print vm.frame_stack[-1].stack
        arguments = [vm.frame_stack[-1].pop() for i in xrange(num_args)][::-1]
        print arguments
        frame = Frame(parameters=arguments, max_stack=code.max_stack, max_locals=code.max_locals)

        vm.frame_stack.append(frame)

        if native_method:
            return_value = native_method(self, vm, method, frame)
        else:
            return_value = vm.run_bytecode(self, method, code.code, frame)

        if frame.raised_exception is not None:
            raise Exception('we dont handle this case yet')

        vm.frame_stack.pop()

        # if it's a non-void method put return value on top of stack
        if method_return_type != 'V':
            assert return_value is not void
            vm.frame_stack[-1].push(return_value)
        else:
            assert return_value is void

        return return_value


    def print_(self):
        print self.constant_pool
        print self.interfaces
        print self.fields
        print self.methods
        print self.attributes

    def __repr__(self):
        return '<Klass %s> ' % self.name

    @staticmethod
    def method_name(*args):
        if isinstance(args[0], Method):
            return '%s__%s' % (args[0].name, args[0].descriptor)
        elif len(args) == 2:
            return '%s__%s' % args
        raise Exception


class NativeClass(Class):
    def get_method(self, method_name, type_signature):
        if method_name in ('<init>', '<clinit>'):
            return Method(ACC_STATIC, method_name, type_signature, [])
        if method_name in self.methods:
            return self.methods[method_name]
        raise NoSuchMethodException('No such method %s.%s (%s)' % (self, method_name, type_signature) )

    def run_method(self, vm, method, method_descriptor):
        args = []
        if (method.access_flags & ACC_STATIC ) == 0:
            # method is not static so load instance
            args.append(vm.stack[-1].pop())
            if args[-1] == null:
                raise Exception('nullpointerexception')

        # parse argument list and return type
        method_arguments, method_return_type = parse_descriptor(method_descriptor)
        # read arguments into stack
        for arg_type in method_arguments:
            arg = vm.stack[-1].pop()
            args.append(arg)

        if method.name in ('<init>', '<clinit>'):
            return void
        return_value = getattr(self, method.name, None)(*args)
        if method_return_type == 'V':
            return void
        return return_value


class ClassInstance(object):
    _klass = None
    _klass_name = None
    _values = None

    def __init__(self, klass_name, klass):
        assert isinstance(klass, Class)
        self._values = {}
        self._klass = klass
        self._klass_name = klass_name

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        if name in  self._values:
            return self._values[name]
        if name in self._klass.methods:
            return self._klass.methods[name]
        raise Exception()

    def __setattr__(self, name, value):
        if name in self.__dict__ or name[0] == '_':
            self.__dict__[name] = value
            return

        # TODO: check the type in the parent class

        self._values[name] = value
        pass

    def __repr__(self):
        if self._klass_name == 'java/lang/String':
            return '<String "%s">' % (''.join(chr(x) for x in self._values['value']))
        return '<Instance of "%s" values:%s>' % (self._klass_name, self._values)

class ArrayClass(object):
    _klass = None

    def __init__(self, klass, size):
        assert isinstance(klass, Class)
        self._klass = klass
        self.array = [None] * size

    @property
    def size(self):
        return len(self.array)
