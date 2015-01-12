import logging

from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException, ClassInstance, Class
from classconstants import *
from descriptor import parse_descriptor
from klasses import primitive_classes
from utils import get_attribute, NoSuchAttributeError

from bytecode import bytecodes

class VM:
    def __init__(self, classpath=[]):
        self.class_cache = {}
        self.class_loader = DefaultClassLoader(classpath)

        self.frame_stack = [Frame()]
        self.heap = []

    def load_class(self, class_name):
        if class_name in self.class_cache:
            return self.class_cache[class_name]
        if class_name in primitive_classes:
            self.class_cache[class_name] = Class(class_name)
            return self.class_cache[class_name]

        klass = self.class_loader.load(class_name)
        self.class_cache[class_name] = klass

        # load all supers and interfaces
        if klass.super_class:
            klass.super_class = self.load_class(klass.super_class)
        klass.interfaces = map(self.load_class, klass.interfaces)

        # run <clinit> method of class
        try:
            self.run_method(klass, klass.get_method('<clinit>', '()V'))
            # initialise this method before running any other code
            self.run_bytecode(len(self.frame_stack)-1)
        except NoSuchMethodException:
            pass

        return klass

    def run_method(self, klass, method):
        klass.run_method(self, method, method.descriptor)


    def constant_pool_index(self, bytecode, index):
        return (bytecode[index+1]<<8) | (bytecode[index+2])

    def resolve_field(self, current_klass, ref_index, expected_field_types=None):
        field_type, field, _  = current_klass.constant_pool.get_object(0, ref_index)
        if expected_field_types:
            assert field_type in expected_field_types
        if field_type == 'String':
            string = ClassInstance('java/lang/String', self.load_class('java/lang/String'))
            string.value = map(ord, current_klass.constant_pool.get_string(field[0]))
            return string
        elif field_type in ('Float', 'Integer'):
            return field[0]
        elif field_type == 'Class':
            return self.load_class(current_klass.constant_pool.get_string(field[0]))
        klass_descriptor = current_klass.constant_pool.get_class(field[0])
        field_name, field_descriptor = current_klass.constant_pool.get_name_and_type(field[1])
        klass = self.load_class(klass_descriptor)
        if field_type in ('Methodref', 'InterfaceMethodref'):
            return klass, klass.get_method(field_name, field_descriptor)
        elif field_type == 'Fieldref':
            return klass, field_name, field_descriptor
        else:
            raise Exception('unknown field type %s' % field_type)

    def throw_exception(self, frame, klass_name):
        exception = self.load_class(klass_name).instantiate()
        frame.push(exception)
        frame.raised_exception = exception

    def handle_exception(self):
        frame = self.frame_stack[-1]
        raised_exception = frame.raised_exception
        if raised_exception is None:
            return

        # unroll the stack to build this eception
        found = False
        while self.frame_stack:
            frame = self.frame_stack[-1]
            print frame.pc
            print 'exception', raised_exception
            print 'current frame', frame
            print 'current frame method', frame.method
            print self.frame_stack
            try:
                exceptions = get_attribute(frame.method, 'CodeAttribute').exceptions
            except NoSuchAttributeError:
                exceptions = []
            for start_pc, end_pc, jump_pc, thrown_class in exceptions:
                if start_pc <= frame.pc < end_pc:
                    print 'thrown class', thrown_class
                    caught = False
                    if thrown_class == 0:
                        caught = True
                    else:
                        klass_name = frame.klass.constant_pool.get_class(thrown_class)
                        resolved_thrown_class = self.load_class(klass_name)
                        caught = resolved_thrown_class.is_subclass(raised_exception)

                    if caught:
                        print 'jumping to', jump_pc
                        frame.push(raised_exception)
                        frame.raised_exception = None
                        frame.pc = jump_pc
                        found = True
                        break
            if found:
                break
            logging.debug('with exception table of %s' % exceptions)
            self.frame_stack.pop()
        if not found:
            print 'Unable to handle exception %s' % raised_exception
            print raised_exception.stacktrace
            sys.exit(1)


    def run_bytecode(self, min_level=1):
        while len(self.frame_stack) > min_level:
            frame = self.frame_stack[-1]
            print self.frame_stack
            print frame.pretty_code(self)
            if frame.method and frame.method.access_flags & ACC_NATIVE:
                return_value = frame.native_method(frame.klass, self, frame.method, frame)
                self.frame_stack.pop()
                print frame.native_method, frame.method.return_type
                if frame.method.return_type != 'V':
                    self.frame_stack[-1].push(return_value)
                else:
                    assert return_value is void
                print 'returning to method %s.%s pc:%d' % (
                        self.frame_stack[-1].klass.name,
                        self.frame_stack[-1].method.name,
                        self.frame_stack[-1].pc)
                continue

            bc = frame.code.code[frame.pc]
            frame.klass = frame.klass
            if bc in bytecodes:
                start, bytecode_function, _, _ = bytecodes[bc]

                # logging
                logging.debug('pc: %d (%s.%s (%s)) calling bytecode %d:%s' %
                        (frame.pc,
                         frame.klass.name,
                         frame.method.name,
                         frame.method.descriptor,
                         bc,
                         bytecode_function.__name__))
                # /logging

                previous_pc = frame.pc
                bytecode_function(
                        self,
                        frame, bc - start,
                        frame.code.code)
                if frame.raised_exception:
                    self.handle_exception()
                else:
                    frame.pc += 1

                if frame.return_value is not None:
                    self.frame_stack.pop()
                    if frame.method.return_type != 'V':
                        self.frame_stack[-1].push(frame.return_value)
            else:
                raise Exception('Unknown bytecode in class %s.%s(%d): %d' % (
                    frame.klass.name,
                    frame.method.name,
                    frame.pc,
                    frame.code.code[frame.pc]))

