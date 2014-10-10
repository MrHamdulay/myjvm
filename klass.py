from constantpool import ConstantPool
from classtypes import CodeAttribute, Method

class NoSuchMethodException(Exception):
    pass

class Class:
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

    def __init__(self):
        self.constant_pool = ConstantPool()
        self.interfaces = []
        self.fields = []
        self.methods = []
        self.attributes = []

    def get_method(self, method_name, type_signature):
        for method in self.methods:
            if method.name == method_name:
                return method
        raise NoSuchMethodException('No such method')

    def print_(self):
        print self.constant_pool
        print self.interfaces
        print self.fields
        print self.methods
        print self.attributes

class NativeClass(Class):
    native_methods = {}
    def get_method(self, method_name, type_signature):
        try:
            return self.native_methods[method_name]
        except KeyError:
            raise NoSuchMethodException()

class ClassInstance:
    def __init__(self, klass):
        self.values = {}

    def putfield(self, field, value):
        self.values[field] = value

    def getfield(self, field):
        return self.values[field]
