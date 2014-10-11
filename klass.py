from constantpool import ConstantPool
from classtypes import CodeAttribute, Method
from classconstants import ACC_STATIC

class NoSuchMethodException(Exception):
    pass

EMPTY_METHOD = Method(ACC_STATIC, '', '()V', [CodeAttribute(0, 0, [], [], [])])

class Class:
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
        self.fields = []
        self.methods = []
        self.attributes = []

    def get_method(self, method_name, type_signature):
        for method in self.methods:
            if method.name == method_name:
                return method
        raise NoSuchMethodException('No such method %s (%s)' % (method_name, type_signature) )

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

class ClassInstance:
    def __init__(self, klass_name, klass):
        self.klass = klass
        self.klass_name = klass_name
        self.values = {}

    def putfield(self, field, value):
        self.values[field] = value

    def getfield(self, field):
        return self.values[field]

    def __repr__(self):
        return '<Instance of %s>' % self.klass_name
