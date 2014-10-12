import logging

from utils import get_attribute
from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException, ClassInstance
from classconstants import *
from descriptor import parse_descriptor

null = 'null', object()
void = 'void', object()

bytecodes = {}
def register_bytecode(start, end=-1):
    def decorator(f):
        if decorator.end == -1:
            decorator.end = decorator.start+1
        for i in xrange(decorator.start, decorator.end+1):
            bytecodes[i] = (decorator.start, f)
        return f
    decorator.start = start
    decorator.end = end
    return decorator

class VM:
    def __init__(self, classpath=[]):
        self.class_cache = {}
        self.class_loader = DefaultClassLoader(classpath)

        # initial empty frame
        self.stack = [Frame()]
        self.heap = []

    def load_class(self, class_name):
        logging.debug( 'loading %s' % class_name)
        if class_name in self.class_cache:
            return self.class_cache[class_name]

        klass = self.class_loader.load(class_name)
        self.class_cache[class_name] = klass

        # load all supers and interfaces
        if klass.super_class:
            self.load_class(klass.super_class)
        for interfaces in klass.interfaces:
            self.load_class(interfaces)

        # run <clinit> method of class
        try:
            self.run_method(klass, klass.get_method('<clinit>', '()V'))
        except NoSuchMethodException:
            pass

        return klass

    def run_method(self, klass, method):
        logging.debug('running method %s' %  str(method))

        # yup, our stack has infinite depth. Contains only frames
        code = get_attribute(method, 'Code')

        #print self.stack[-1].stack
        frame = Frame(max_stack=code.max_stack, max_locals=code.max_locals)
        locals_index=0
        if (method.access_flags & ACC_STATIC ) == 0:
            # method is not static so load instance
            frame.insert_local(locals_index, self.stack[-1].pop())
            locals_index+=1

        # parse argument list and return type
        method_arguments, method_return_type = parse_descriptor(method.descriptor)
        # read arguments into stack
        for arg_type in method_arguments:
            arg = self.stack[-1].pop()
            frame.insert_local(locals_index, arg)
            locals_index +=1
        self.stack.append(frame)

        return_value = self.run_bytecode(klass, method, code.code, frame)

        # TODO: check for frame return value somehow

        self.stack.pop()
        # if it's a non-void method put return value on top of stack
        if method_return_type != 'V':
            self.stack[-1].push(return_value)
        else:
            assert return_value is void
        return return_value

    def constant_pool_index(self, bytecode, index):
        return (bytecode[index+1]<<8) | (bytecode[index+2])

    def resolve_field(self, current_klass, ref_index, expected_field_types=None):
        field_type, field  = current_klass.constant_pool.get_object(0, ref_index)
        if expected_field_types:
            assert field_type in expected_field_types
        if field_type == 'String':
            return current_klass.constant_pool.get_string(field[0])
        klass_descriptor = current_klass.constant_pool.get_class(field[0])
        field_name, field_descriptor = current_klass.constant_pool.get_name_and_type(field[1])
        klass = self.load_class(klass_descriptor)
        if field_type == 'Methodref':
            return klass, klass.get_method(field_name, field_descriptor)
        elif field_type == 'Fieldref':
            return field_name, field_descriptor
        else:
            raise Exception('unknown field type %s' % field_type)


    def run_bytecode(self, current_klass, method, bytecode, frame):
        pc = 0
        while pc < len(bytecode):
            print method.name, method.descriptor
            print frame.stack
            bc = bytecode[pc]
            logging.debug('bytecode %d'  % bc)
            if bc in bytecodes:
                start, bytecode_function = bytecodes[bc]
                logging.debug('calling bytecode %s' % bytecode_function.__name__)
                print pc
                ret = bytecode_function(self, current_klass, method, frame, bc - start, bytecode, pc)
                if ret:
                    pc = ret
                else:
                    pc += 1
                if frame.return_value:
                    return frame.return_value
                continue
            elif bc == 178:
                logging.debug('getstatic')
                ref_index = self.constant_pool_index(bytecode, pc)
                field = self.resolve_field(current_klass, ref_index)
                frame.push(field)
            elif bc == 181:
                logging.debug('putfield')
                field_index = self.constant_pool_index(bytecode, pc)
                pc += 2
                field_name, field_descriptor = self.resolve_field(current_klass,
                        field_index, 'Fieldref')
                value, objectref = frame.pop(), frame.pop()
                assert isinstance(objectref, ClassInstance)
                objectref.__setattr__(field_name, value)
            # invokespecial / virtual
            elif bc in (182, 183):
                if bc == 182: logging.debug('invokevirtual')
                if bc == 183: logging.debug( 'invokespecial')
                method_index = self.constant_pool_index(bytecode, pc)
                pc += 2
                klass, method = self.resolve_field(current_klass, method_index)
                self.run_method(klass, method)

            # new
            elif bc == 187:
                logging.debug( 'new')
                klass_index = self.constant_pool_index(bytecode, pc)
                pc += 2
                klass_name = current_klass.constant_pool.get_class(klass_index)
                klass = self.load_class(klass_name)
                instance = ClassInstance(klass_name, klass)
                frame.push(instance)
            else:
                raise Exception('Unknown bytecode in class %s.%s: %d' % (klass.name, method.name, bytecode[pc]))
            pc += 1
        return void

import bytecode
