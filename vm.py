import logging

from utils import get_attribute
from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException, ClassInstance
from classconstants import ACC_STATIC
from descriptor import parse_descriptor

null = object()
void = object()

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

        if method.access_flags | ACC_STATIC:
            this = None
        else:
            this = None
        frame = Frame(this=this, max_stack=code.max_stack, max_locals=code.max_locals)

        # parse argument list and return type
        method_arguments, method_return_type = parse_descriptor(method.descriptor)
        # read arguments into stack
        for i, arg_type in enumerate(method_arguments):
            arg = self.stack[-1].pop()
            frame.insert_local(i+1, arg)
        self.stack.append(frame)

        return_value = self.run_bytecode(klass, method, code.code, frame)

        # TODO: check for frame return value somehow

        self.stack.pop()
        # if it's a non-void method put return value on top of stack
        if method_return_type != 'V':
            self.stack[-1].push(return_value)
        return return_value

    def constant_pool_index(self, bytecode, index):
        return (bytecode[index+1]<<8) | (bytecode[index+2])

    def run_bytecode(self, current_klass, method, bytecode, frame):
        pc = 0
        while pc < len(bytecode):
            bc = bytecode[pc]
            # iconst_<n>
            if 2 <= bc <= 8:
                logging.debug( 'iconst')
                frame.push(bc-2-1)
            # istore_<n>
            elif 59 <= bc <= 62:
                logging.debug( 'istore')
                frame.insert_local(bc - 59, frame.pop())
            # aload_<n>
            elif 42 <= bc <= 45:
                logging.debug( 'aload')
                n = bc - 42
                frame.push(frame.local_variables[n])
            # astore_<n>
            elif 75 <= bc <= 78:
                logging.debug('astore')
                reference = frame.pop()
                assert isinstance(reference, ClassInstance)
                frame.insert_local(bc-75, reference)
            # dup
            elif bc == 89:
                logging.debug( 'dup')
                frame.push(frame.stack[-1])
            # return
            elif bc == 177:
                logging.debug( 'return')
                # TODO: parse out the return type and assert void
                # TODO: if synchronized method exit the monitor
                return void
            # invokespecial / virtual
            elif bc in (182, 183):
                if bc == 182: logging.debug('invokevirtual')
                if bc == 183: logging.debug( 'invokespecial')
                method_index = self.constant_pool_index(bytecode, pc)
                pc += 2
                klass_descriptor, method_name, method_descriptor = current_klass.constant_pool.get_method(method_index)
                klass = self.load_class(klass_descriptor)
                method = klass.get_method(method_name, method_descriptor)
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
                raise Exception('Unknown bytecode: %d' % bytecode[pc])
            pc += 1

