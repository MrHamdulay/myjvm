import sys
import logging
import os.path

from classreader import ClassReader
from vm import VM

class Interpreter:
    def __init__(self, initial_class, classpath):
        self.initial_class_name = initial_class
        self.vm = VM(classpath)

    def start(self):
        klass = self.vm.load_class(self.initial_class_name)
        self.vm.stack[0].push('java')

        # run initial method
        self.vm.run_method(klass, klass.get_method('main', ''))



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) != 2:
        print 'Usage: interpreter.py <class>'
        sys.exit(0)
    classpath=[]
    dir, classname = os.path.split(sys.argv[1])
    if os.path.isdir(dir):
        classpath.append(dir)

    interpreter = Interpreter(classname, classpath)
    interpreter.start()
