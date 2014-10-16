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
    name = None

    major_version = None
    minor_version = None

    constant_pool = None
    access_flags = None
    this_class = None
    super_class = None

    interfaces = None
    fields = None
    methods = None
    attributes = None

    def __init__(self, name=None):
        self.name = name if name else self.__class__.__name__
        self.constant_pool = ConstantPool()
        self.interfaces = []
        self.fields = {}
        self.methods = {}
        self.attributes = []

    def get_method(self, method_name, type_signature):
        if method_name in self.methods:
            return self.methods[method_name]
        raise NoSuchMethodException('No such method %s (%s)' % (method_name, type_signature) )

    def instantiate(self):
        return ClassInstance(self.method_name, self)

    def run_method(self, vm, method, method_descriptor):
        native_method = None
        # handle native methods
        if (method.access_flags & ACC_NATIVE) != 0:
            try:
                native_method = getattr(classes_with_natives[self.name], method.name)
            except AttributeError:
                raise Exception('Missing method %s on class %s' % (method.name, self.name))
            method.attributes.append(CodeAttribute(100, 100, [], [], []))
        # yup, our stack has infinite depth. Contains only frames
        code = get_attribute(method, 'Code')

        frame = Frame(max_stack=code.max_stack, max_locals=code.max_locals)
        locals_index=0
        if (method.access_flags & ACC_STATIC ) == 0:
            # method is not static so load instance
            frame.insert_local(locals_index, vm.stack[-1].pop())
            locals_index+=1

        # parse argument list and return type
        method_arguments, method_return_type = parse_descriptor(method.descriptor)
        # read arguments into stack
        for arg_type in method_arguments:
            arg = vm.stack[-1].pop()
            frame.insert_local(locals_index, arg)
            locals_index +=1
        vm.stack.append(frame)

        if native_method:
            return_value = native_method(self, vm, method, frame)
        else:
            return_value = vm.run_bytecode(self, method, code.code, frame)

        # TODO: check for frame return value somehow

        vm.stack.pop()
        # if it's a non-void method put return value on top of stack
        if method_return_type != 'V':
            vm.stack[-1].push(return_value)
        else:
            assert return_value is void
        return return_value


    def print_(self):
        print self.constant_pool
        print self.interfaces
        print self.fields
        print self.methods
        print self.attributes


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
        raise Exception

    def __setattr__(self, name, value):
        if name in self.__dict__ or name[0] == '_':
            self.__dict__[name] = value
            return

        # TODO: check the type in the parent class

        self._values[name] = value
        pass

    def __repr__(self):
        return '<Instance of %s>' % self._klass_name
