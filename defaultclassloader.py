import os.path

from classreader import ClassReader

class DefaultClassLoader:
    def __init__(self):
        self.classpath = ['.']
        pass

    def load(self, classname):
        parts = classname.split('.')

        class_file = None
        for classpath in self.classpath:
            class_filename = os.path.join(*([classpath]+parts))+'.class'
            if os.path.isfile(class_filename):
                class_file = open(class_filename)
                break
        else:
            raise Exception('class file not found')

        klass = ClassReader(class_file).klass
        klass.__str__()
        return klass
