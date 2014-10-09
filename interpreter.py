import sys

from classreader import ClassReader
from defaultclassloader import DefaultClassLoader

class Interpreter:
    def __init__(self, initial_class):
        self.class_cache = {}
        self.class_loader = DefaultClassLoader()
        self.initial_class_name = initial_class

    def load_class(self, class_name):
        print 'loading', class_name
        if class_name in self.class_cache:
            return self.class_cache[class_name]

        klass = self.class_loader.load(self.initial_class_name)
        self.class_cache[class_name] = klass

        # load all supers and interfaces
        self.load_class(klass.super_class)
        for interfaces in klass.interfaces:
            self.load_class(interfaces)

        # run <init> method of class
        self.run_method(klass, klass.get_method('<init>', '()V'))

        return klass

    def start(self):
        klass = self.load_class(self.initial_class_name)

        # run initial method
        self.run_method(klass, klass.get_method('main', ''))

    def run_method(self, klass, method):
        pass



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: interpreter.py <class>'
        sys.exit(0)
    initial_class = sys.argv[1]
    interpreter = Interpreter(initial_class)
    interpreter.start()
