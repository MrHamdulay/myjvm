import logging

class StackOverflowException(Exception):
    pass

class Frame:
    operand_stack = None
    local_variables = None

    def __init__(self, this=None, parameters=[], max_stack=1, max_locals=0):
        self.stack = []
        self.local_variables = [None] * max_locals
        self.return_value = None
        i=0
        if this:
            self.local_variables[i] = this
            i+=1
        for param in parameters:
            self.local_variables[i] = param
            i += 1
        self.max_stack=max_stack
        self.max_locals=max_locals

    def push(self, value):
        assert value is not None
        self.stack.append(value)
        if len(self.stack) > self.max_stack:
            print self.stack
            raise StackOverflowException('%s > %d' % (len(self.stack), self.max_stack))

    def pop(self):
        return self.stack.pop()

    def insert_local(self, index, value):
        self.local_variables[index] = value

    def get_local(self, index):
        return self.local_variables[index]

    def __repr__(self):
        return '<Frame stack:%d vars:%d>' % (len(self.stack), len(self.local_variables))
