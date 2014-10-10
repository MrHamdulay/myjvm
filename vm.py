from utils import get_attribute
from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException, ClassInstance
from classconstants import ACC_STATIC

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
        print 'loading', class_name
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
        print 'running method', method
        # yup, our stack has infinite depth. Contains only frames
        code = get_attribute(method, 'Code')

        if method.access_flags | ACC_STATIC:
            this = None
        else:
            this = None
        frame = Frame(this=this, max_stack=code.max_stack, max_locals=code.max_locals)
        self.stack.append(frame)

        return_value = self.run_bytecode(klass, method, code.code, frame)

        # TODO: check for frame return value somehow

        self.stack.pop()
        return return_value

    def constant_pool_index(self, bytecode, index):
        return (bytecode[index+1]<<8) | (bytecode[index+2])

    def run_bytecode(self, current_klass, method, bytecode, frame):
        pc = 0
        while pc < len(bytecode):
            bc = bytecode[pc]
            # iconst_<n>
            if 2 <= bc <= 8:
                frame.push(bc-2-1)
            # istore_<n>
            elif 59 <= bc <= 62:
                frame.insert_local(bc - 59, frame.pop())
            # aload_<n>
            elif 42 <= bc <= 45:
                n = 45 - bc
                frame.stack.push(frame.local_variables[n])
            # dup
            elif bc == 89:
                frame.push(frame.stack[-1])
            # return
            elif bc == 177:
                # TODO: parse out the return type and assert void
                # TODO: if synchronized method exit the monitor
                return void
            # invokespecial
            elif bc == 183:
                method_index = self.constant_pool_index(bytecode, pc)
                pc += 2
                klass_descriptor, method_name, method_descriptor = current_klass.constant_pool.get_method(method_index)
                print klass_descriptor, method_name, method_descriptor
                raise Exception

            # new
            elif bc == 187:
                klass_index = self.constant_pool_index(bytecode, pc)
                pc += 2
                klass = current_klass.constant_pool.get_class(klass_index)
                instance = ClassInstance(klass)
                frame.push(instance)
            else:
                raise Exception('Unknown bytecode: %d' % bytecode[pc])
            pc += 1

