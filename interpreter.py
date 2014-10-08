import sys

from classreader import ClassReader
from defaultclassloader import DefaultClassLoader

class Interpreter:
    def __init__(self, initial_class):
        self.initial_class_name = initial_class

    def run(self):
        classloader = DefaultClassLoader()
        klass = classloader.load(self.initial_class_name)
        print klass



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Usage: interpreter.py <class>'
        sys.exit(0)
    initial_class = sys.argv[1]
    interpreter = Interpreter(initial_class)
    interpreter.run()
