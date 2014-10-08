from classconstants import *

class ConstantPoolException(Exception):
    pass

class ConstantPool:
    def __init__(self):
        self.constant_pool = []

    def add_pool(self, *args):
        self.constant_pool.append(args)

    def get_string(self, index):
        if self.constant_pool[index][0] == CONSTANT_Utf8:
            raise ConstantPoolException()
        return self.constant_pool[index][1]
