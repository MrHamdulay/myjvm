import logging
from classconstants import ACC_NATIVE

class StackOverflowException(Exception):
    pass

class Frame:
    operand_stack = None
    local_variables = None

    def __init__(self, this=None, parameters=[], max_stack=1, max_locals=0, klass=None, method=None, native_method=None, code=None):
        self.stack = []
        self.local_variables = [None] * max_locals

        self.raised_exception = None
        self.return_value = None
        self.pc = 0

        self.max_stack=max_stack
        self.max_locals=max_locals

        self.klass = klass
        self.method = method
        if klass or method:
            assert method.access_flags & ACC_NATIVE == (ACC_NATIVE if native_method else 0)
        self.native_method = native_method
        self.code = code

        i=0
        if this:
            self.local_variables[i] = this
            i+=1
        self.local_variables[i:len(parameters)+i] = parameters

    def push(self, value):
        assert value is not None
        self.stack.append(value)
        if len(self.stack) > self.max_stack:
            raise StackOverflowException('%s > %d (%s)' % (len(self.stack), self.max_stack, self.stack))

    def pop(self):
        return self.stack.pop()

    def insert_local(self, index, value):
        self.local_variables[index] = value

    def get_local(self, index):
        return self.local_variables[index]

    def __repr__(self):
        return '<Frame %s.%s stack:%d vars:%d%s>' % (self.klass.name if self.klass else '', self.method.name if self.method else '', len(self.stack), len(self.local_variables), ' native' if self.native_method else '')
