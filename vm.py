from utils import get_attribute
from defaultclassloader import DefaultClassLoader
from frame import Frame
from klass import NoSuchMethodException

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
        frame = Frame(max_stack=code.max_stack, max_locals=code.max_locals)
        self.stack.append(frame)

        self.run_bytecode(code.code, frame)

        # TODO: check for frame return value somehow

        self.stack.pop()

    def run_bytecode(self, bytecode, frame):
        pc = 0
        while pc < len(bytecode):
            raise Exception('Unknown bytecode: %d' % bytecode[pc])
            # aload_<n>
            if 42 <= bytecode[pc] <= 45:
                n = 45 - bytecode[pc]
                frame.stack.push(frame.local_variables[n])
            pc += 1

