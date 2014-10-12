from constantpool import ConstantPool
from classtypes import CodeAttribute, Method
from classconstants import ACC_STATIC

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

    def print_(self):
        print self.constant_pool
        print self.interfaces
        print self.fields
        print self.methods
        print self.attributes


class NativeClass(Class):
    native_methods = {}
    def get_method(self, method_name, type_signature):
        if method_name == '<init>':
            return EMPTY_METHOD
        try:
            return self.native_methods[method_name]
        except KeyError:
            raise NoSuchMethodException('No such method %s (%s)' % (method_name, type_signature) )

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
