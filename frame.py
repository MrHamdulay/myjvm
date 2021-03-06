from __future__ import absolute_import
import logging
from classconstants import ACC_NATIVE, ACC_STATIC

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

        self.max_stack = max_stack
        self.max_locals = max_locals

        self.klass = klass
        self.method = method
        '''if klass or method:
            assert method.access_flags & ACC_NATIVE == (
                ACC_NATIVE if native_method else 0)'''
        self.native_method = native_method
        self.code = code

        i = 0
        if method and method.access_flags & ACC_STATIC == 0:
            self.local_variables[0] = parameters.pop(0)
            i += 1

        if method and method.parameters:
            for j, (value, parameter) in enumerate(zip(parameters[-len(method.parameters):], method.parameters)):
                self.local_variables[i+j] = value
                if parameter in 'JD':
                    i += 1
                    self.local_variables[i+j] = 'extra'
        else:
            assert not parameters

    def push(self, value):
        assert value is not None
        self.stack.append(value)
        if len(self.stack) > self.max_stack:
            raise StackOverflowException('%s > %d (%s)' %
                    (len(self.stack), self.max_stack, self.stack))

    def pop(self):
        return self.stack.pop()

    def insert_local(self, index, value):
        assert value is not None
        self.local_variables[index] = value

    def get_local(self, index):
        value = self.local_variables[index]
        assert value is not None
        return value

    def __repr__(self):
        return '<Frame %s.%s pc:%d%s>' % (
                self.klass.name if self.klass else '',
                self.method.name if self.method else '',
                self.pc,
                ' native' if self.native_method else '')

    def pretty_code(self, vm, around=-1):
        if not self.code.code:
            return ''
        output = 'Bytecode for method: %s.%s %s\n' % (
            self.klass.name if self.klass else '',
            self.method.name if self.method else '',
            self.method.descriptor if self.method else '')

        skip = 0
        start = max(0, self.pc-10)
        end = min(len(self.code.code), self.pc+10)
        for i, code in enumerate(self.code.code):
            single_output = ''
            if skip:
                skip -= 1
            elif code in bytecodes:
                begin, f, skip, repr_f = bytecodes[code]
                single_output += '%d: %s %s\n' % (i, f.func_name,
                        '\t\t***' if self.pc == i else '')
                if repr_f:
                    try:
                        single_output += 'repr: %s\n' % repr_f(
                                vm, self, i, code-begin, self.code.code)
                    except Exception as e:
                        single_output += 'repr: Exception :( '+str(e)
            else:
                single_output += '%d: unknown bytecode %d\n' % (i, code)
                print output
                raise Exception
            if abs(i-self.pc) < around or around == -1:
                output += single_output

        return output

from bytecode import bytecodes
