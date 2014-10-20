import sys
#import logging
#import os.path

from classreader import ClassReader
from vm import VM

class Interpreter:
    def __init__(self, initial_class, classpath):
        self.initial_class_name = initial_class
        self.vm = VM(classpath)

    def start(self):
        self.vm.class_loader.load_jar('klasses/rt.jar')
        klass = self.vm.load_class(self.initial_class_name)
        self.vm.stack[0].push('java')

        # run initial method
        self.vm.run_method(klass, klass.get_method('main', ''))



def entry_point(argv):
    #logging.basicConfig(level=logging.DEBUG)
    if len(argv) != 2:
        print 'Usage: interpreter.py <class>'
        return 1
    classpath=['.']
    path_parts = argv[1].split('/')
    dir, classname = '/'.join(path_parts[:-1]), path_parts[-1]
    classpath.append(str(dir))

    interpreter = Interpreter(classname, classpath)
    interpreter.start()

    return 0

def target(*args):
    return entry_point, None

if __name__ == '__main__':
    entry_point(sys.argv)
