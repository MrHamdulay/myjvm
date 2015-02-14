from __future__ import absolute_import
from classconstants import *

class ConstantPoolException(Exception):
    pass

class ConstantPoolItem:
    def __init__(self, tag, ints, strings=[]):
        self.tag = tag
        self.ints = ints
        self.strings = strings

class ConstantPool:
    def __init__(self, size):
        self.constant_pool = [[]]*size
        self.size = 0

    def add_pool(self, item):
        self.constant_pool[self.size] = item
        self.size += 1
        if item.tag in (CONSTANT_Double, CONSTANT_Long):
            self.constant_pool[self.size] = ConstantPoolItem(CONSTANT_Utf8, [], ['blank'])
            self.size += 1

    def get_string(self, index):
        return self.get_object(CONSTANT_Utf8, index)[1][0]

    def get_class_name(self, index):
        class_info = self.get_object(CONSTANT_Class, index)[0]
        return self.get_string(class_info[0])

    def get_class(self, index):
        klass = self.get_object(CONSTANT_Class, index)
        return self.get_string(klass[0][0])

    def get_name_and_type(self, index):
        name_and_type = self.get_object(CONSTANT_NameAndType, index)[0]
        return self.get_string(name_and_type[0]), self.get_string(name_and_type[1])


    def get_method(self, index, type_tag=CONSTANT_Methodref):
        methodref = self.get_object(type_tag, index)[1]

        klass_descriptor = self.get_class(methodref[0])
        name, type_ = self.get_name_and_type(methodref[1])
        return klass_descriptor, name, type_

    def get_object(self, type, index):
        constant = self.constant_pool[index-1]
        if not isinstance(type, (list, tuple)):
            type = (type, )
        if constant.tag not in type and 0 not in type :
            name = ' or '.join(CONSTANT_POOL_NAMES[x] for x in type)
            raise ConstantPoolException('Expected %s got %s(%s) %s %s' % (
                name,
                CONSTANT_POOL_NAMES[constant.tag],
                str(type),
                constant.ints,
                constant.strings))
        if 0 in type:
            return CONSTANT_POOL_NAMES[constant.tag-1], constant.ints, constant.strings
        return constant.ints, constant.strings

    def __repr__(self):
        result = ''
        for i, constant in enumerate(self.constant_pool):
            result += '%d %s %s' % (i+1, CONSTANT_POOL_NAMES[constant.tag-1],  ' '.join(map(str, constant.ints)) +' '.join(map(str, constant.strings)) +'\n')
        return result
