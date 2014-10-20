import logging

from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException, ClassInstance
from classconstants import *
from descriptor import parse_descriptor
from klasses import builtin_classes

from bytecode import bytecodes

class VM:
    def __init__(self, classpath=[]):
        self.class_cache = {}
        self.class_loader = DefaultClassLoader(classpath)

        # initial empty frame
        self.stack = [Frame()]
        self.heap = []

    def load_class(self, class_name):
        if class_name in builtin_classes:
            return builtin_classes[class_name]
        if class_name in self.class_cache:
            return self.class_cache[class_name]

        logging.debug( 'loading %s' % class_name)
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
        logging.debug('running method %s.%s' %  (klass.name, str(method)))
        klass.run_method(self, method, method.descriptor)


    def constant_pool_index(self, bytecode, index):
        return (bytecode[index+1]<<8) | (bytecode[index+2])

    def resolve_field(self, current_klass, ref_index, expected_field_types=None):
        field_type, field  = current_klass.constant_pool.get_object(0, ref_index)
        if expected_field_types:
            assert field_type in expected_field_types
        if field_type == 'String':
            string = ClassInstance('java/lang/String', self.load_class('java/lang/String'))
            string.value = map(ord, current_klass.constant_pool.get_string(field[0]))
            return string
        elif field_type in ('Float', 'Integer'):
            return field[0]
        klass_descriptor = current_klass.constant_pool.get_class(field[0])
        field_name, field_descriptor = current_klass.constant_pool.get_name_and_type(field[1])
        klass = self.load_class(klass_descriptor)
        if field_type == 'Methodref':
            return klass, klass.get_method(field_name, field_descriptor)
        elif field_type == 'Fieldref':
            return klass, field_name, field_descriptor
        else:
            raise Exception('unknown field type %s' % field_type)


    def run_bytecode(self, current_klass, method, bytecode, frame):
        pc = 0
        while pc < len(bytecode):
            logging.debug( 'stackframe %s'% frame.stack)
            bc = bytecode[pc]
            if bc in bytecodes:
                start, bytecode_function, has_constant_pool_index = bytecodes[bc]
                logging.debug('pc: %d (%s.%s) calling bytecode %s' % (pc, current_klass.name, method.name, bytecode_function.__name__))
                if has_constant_pool_index:
                    logging.debug('with constant pool argument %s' %
                            (current_klass.constant_pool.get_object(0, self.constant_pool_index(bytecode, pc)), ))

                ret = bytecode_function(self, current_klass, method, frame, bc - start, bytecode, pc)
                if ret:
                    pc = ret
                pc += 1
                if frame.return_value:
                    return frame.return_value
            else:
                raise Exception('Unknown bytecode in class %s.%s: %d' % (current_klass.name, method.name, bytecode[pc]))
        return void
