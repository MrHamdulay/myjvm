from __future__ import absolute_import
import logging
import exceptions
import sys

from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException, ClassInstance, Class
from classconstants import *
from descriptor import parse_descriptor
from klasses import primitive_classes
from utils import get_attribute, NoSuchAttributeError, make_string
from arithmetic import *

from bytecode import bytecodes

class VM:
    def __init__(self, classpath=[]):
        self.class_cache = {}
        self.class_loader = DefaultClassLoader(classpath)

        self.frame_stack = [Frame()]
        self.heap = []


    @property
    def stack(self):
        return self.frame_stack[-1]

    def warmup(self):
        self.init_native_classes()
        self.load_class('java/lang/Thread')
        System = self.load_class('java/lang/System')
        self.load_class('java/nio/charset/Charset')

        System.registerStreams(
                System,
                self)
        #self.load_class('java/lang/Class$Atomic')
        #self.load_class('java/lang/String')

    def load_class(self, class_name):
        java_Class = None
        if class_name[0] == 'L' and class_name[-1] == ';':
            class_name = class_name[1:-1]
        if class_name != 'java/lang/Class':
            java_Class = self.load_class('java/lang/Class')
        if class_name in self.class_cache:
            return self.class_cache[class_name]
        if class_name in primitive_classes:
            return primitive_classes[class_name]

        if class_name[0] == '[':
            self.class_cache[class_name] = klass = Class.array_factory(class_name)
            klass.super_class = java_Class
            klass.java_instance = java_Class.instantiate()
            klass.java_instance._values['class_name'] = class_name
            return klass

        klass = self.class_loader.load(class_name)
        self.class_cache[class_name] = klass
        if not java_Class:
            java_Class = klass
        klass._klass = java_Class
        klass.java_instance = java_Class.instantiate()
        klass.java_instance._values['class_name'] = class_name

        # load all supers and interfaces
        if klass.super_class:
            klass.super_class = self.load_class(klass.super_class)
        klass.interfaces = map(self.load_class, klass.interfaces)

        # run <clinit> method of class
        try:
            _, method = klass.get_method('<clinit>', '()V')
            self.wrap_run_method(klass, method)
        except NoSuchMethodException:
            pass

        return klass

    def run_method(self, klass, method):
        klass.run_method(self, method, method.descriptor)

    def wrap_run_method(self, instance, method, *args):
        klass = instance
        frame = Frame(max_locals=1)
        if isinstance(instance, ClassInstance):
            klass = instance._klass
            frame.push(instance)
        if args:
            frame.stack += args
        self.frame_stack.append(frame)
        self.run_method(klass, method)
        self.run_bytecode()
        self.frame_stack.pop()
        if frame.stack:
            return frame.stack.pop()
        return void

    def constant_pool_index(self, bytecode, index):
        return (bytecode[index+1]<<8) | (bytecode[index+2])

    def resolve_field(self, current_klass, ref_index, expected_field_types=None):
        field_type, field, _  = current_klass.constant_pool.get_object(0, ref_index)
        if expected_field_types:
            assert field_type in expected_field_types, '%s is not the expected field type' % field_type
        if field_type == 'String':
            s = current_klass.constant_pool.get_string(field[0])
            return make_string(self, s)
        elif field_type == 'Integer':
            return intmask(field[0])
        elif field_type == 'Float':
            return field[0]
        elif field_type == 'Class':
            return self.load_class(current_klass.constant_pool.get_string(field[0])).java_instance
        klass_descriptor = current_klass.constant_pool.get_class(field[0])
        field_name, field_descriptor = current_klass.constant_pool.get_name_and_type(field[1])
        klass = self.load_class(klass_descriptor)
        if field_type in ('Methodref', 'InterfaceMethodref'):
            return klass.get_method(field_name, field_descriptor)
        elif field_type == 'Fieldref':
            return klass, field_name, field_descriptor
        else:
            raise Exception('unknown field type %s' % field_type)

    def throw_exception(self, frame, klass_name, descriptor='()V', *args):
        klass = self.load_class(klass_name)
        exception = klass.instantiate()
        self.wrap_run_method(exception, klass.methods['<init>__'+descriptor], *args)
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
            try:
                exceptions = get_attribute(frame.method, 'CodeAttribute').exceptions
            except NoSuchAttributeError:
                exceptions = []
            for start_pc, end_pc, jump_pc, thrown_class in exceptions:
                if start_pc <= frame.pc < end_pc:
                    caught = False
                    if thrown_class == 0:
                        caught = True
                    else:
                        klass_name = frame.klass.constant_pool.get_class(thrown_class)
                        resolved_thrown_class = self.load_class(klass_name)
                        caught = resolved_thrown_class.is_subclass(raised_exception)

                    if caught:
                        frame.push(raised_exception)
                        frame.raised_exception = None
                        frame.pc = jump_pc
                        found = True
                        break
            if found:
                break
            self.frame_stack.pop()
        if not found:
            print 'Unable to handle exception %s' % raised_exception
            #print raised_exception.stacktrace
            sys.exit(1)
        print self.frame_stack


    def run_bytecode(self):
        min_level = len(self.frame_stack)-1
        while len(self.frame_stack) > min_level:
            frame = self.frame_stack[-1]
            #print
            print 'frame stack', self.frame_stack
            print 'stack stack', [unicode(x).encode('utf-8') for x in frame.stack]
            print 'local variables', repr(frame.local_variables)
            print
            #print frame.pretty_code(self)
            if frame.method and frame.native_method is not None:
                return_value = frame.native_method(
                        frame.klass, self, frame.method, frame)
                if frame.raised_exception:
                    self.handle_exception()
                else:
                    self.frame_stack.pop()
                    if frame.method.return_type != 'V':
                        self.frame_stack[-1].push(return_value)
                    else:
                        assert return_value is void
                #print 'returning to method %s.%s pc:%d return value %s' % (
                #        self.frame_stack[-1].klass.name,
                #        self.frame_stack[-1].method.name,
                #        self.frame_stack[-1].pc,
                #        return_value)
                continue

            if frame.method.access_flags & ACC_STATIC == 0:
                assert frame.klass.is_subclass(frame.local_variables[0])

            bc = frame.code.code[frame.pc]
            if bc in bytecodes:
                start, bytecode_function, _, bc_repr = bytecodes[bc]

                # logging
                r = ''
                if bc_repr:
                    r = 'repr: %s' % bc_repr(self, frame, frame.pc,
                             bc-start, frame.code.code)

                logging.debug('pc: %d (%s.%s (%s)) calling bytecode %d:%s' %
                        (frame.pc,
                         frame.klass.name,
                         frame.method.name,
                         frame.method.descriptor,
                         bc,
                         bytecode_function.__name__
                         ))
                logging.debug(r)
                # /logging

                previous_pc = frame.pc
                bytecode_function(
                        self,
                        frame, bc - start,
                        frame.code.code)
                if frame.raised_exception:
                    #print frame.pretty_code(self, around=20)
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

    def init_native_classes(self):
        pc = primitive_classes
        for type in 'Ddouble Bbyte Cchar Ffloat Iint Jlong Sshort Zboolean'.split():
            name = type[1:]
            klass = Class(name)
            klass.java_instance = self.load_class('java/lang/Class').instantiate()
            klass.java_instance._values['class_name'] = name
            klass.primitive = True
            pc[type[0]] = pc[name] = klass
