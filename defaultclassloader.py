import os.path

from klasses import native_classes
from classreader import ClassReader

class DefaultClassLoader:
    def __init__(self, classpath=[]):
        self.classpath = ['.'] + classpath
        pass

    def load(self, classname):
        if classname in native_classes:
            return native_classes[classname]
        parts = classname.split('/')

        class_file = None
        for classpath in self.classpath:
            class_filename = os.path.join(*([classpath]+parts))+'.class'
            if os.path.isfile(class_filename):
                class_file = open(class_filename)
                break
        else:
            raise Exception('class file not found: %s' % classname)

        klass = ClassReader(classname, class_file).klass
        return klass
