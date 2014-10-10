from classconstants import *

class ConstantPoolException(Exception):
    pass

class ConstantPool:
    def __init__(self):
        self.constant_pool = []

    def add_pool(self, *args):
        self.constant_pool.append(*args)

    def get_string(self, index):
        return self.get_object(CONSTANT_Utf8, index)[0]

    def get_class(self, index):
        klass = self.get_object(CONSTANT_Class, index)
        return self.get_string(klass[0])

    def get_name_and_type(self, index):
        name_and_type = self.get_object(CONSTANT_NameAndType, index)
        return self.get_string(name_and_type[0]), self.get_string(name_and_type[1])


    def get_method(self, index):
        methodref = self.get_object(CONSTANT_Methodref, index)

        klass_descriptor = self.get_class(methodref[0])
        name, type_ = self.get_name_and_type(methodref[1])
        return klass_descriptor, name, type_

    def get_object(self, type, index):
        constant = self.constant_pool[index-1]
        if type != constant[0] and type != 0:
            raise ConstantPoolException('Expected %s got %s(%d) %s' % (CONSTANT_POOL_NAMES[type-1], CONSTANT_POOL_NAMES[constant[0]-1], type, constant[1:]))
        return constant[1:]

    def __repr__(self):
        result = ''
        for i, constant in enumerate(self.constant_pool):
            result += '%d %s %s' % (i, CONSTANT_POOL_NAMES[constant[0]-1],  ' '.join(map(str, constant[1:])) +'\n')
        return result
