from classconstants import *

class ConstantPoolException(Exception):
    pass

class ConstantPool:
    def __init__(self):
        self.constant_pool = []

    def add_pool(self, *args):
        self.constant_pool.append(*args)

    def get_string(self, index):
        constant = self.constant_pool[index-1]
        if constant[0] != CONSTANT_Utf8:
            raise ConstantPoolException('Expected UTF8 got %s %s' % (CONSTANT_POOL_NAMES[constant[0]-1], constant[1:]))
        return constant[1]

    def get_class(self, index):
        constant = self.constant_pool[index-1]
        if constant[0] != CONSTANT_Class:
            raise ConstantPoolException('Expected Class got %s %s' % (CONSTANT_POOL_NAMES[constant[0]-1], constant[1:]))
        return self.get_string(constant[1])

    def get_object(self, index):
        return self.constant_pool[index-1][1]

    def __repr__(self):
        result = ''
        for i, constant in enumerate(self.constant_pool):
            result += '%d %s %s' % (i, CONSTANT_POOL_NAMES[constant[0]-1],  ' '.join(map(str, constant[1:])) +'\n')
        return result
