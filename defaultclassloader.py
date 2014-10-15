import os.path
from zipfile import ZipFile

from klasses import native_classes
from classreader import ClassReader

class DefaultClassLoader:
    def __init__(self, classpath=[]):
        self.classpath = ['.'] + classpath
        self.lazy_classes = {}
        pass

    def load_jar(self, jarfilename):
        jar = ZipFile(jarfilename)
        for classname in jar.namelist():
            if not classname.endswith('.class'):
                continue
            self.lazy_classes[classname.split('.class')[0]] = jar

    def load_class_from_jar(self, classname):
        return self.lazy_classes[classname].open(classname+'.class', 'r')


    def load(self, classname):
        if classname in native_classes:
            return native_classes[classname]

        class_file = None

        if classname in self.lazy_classes:
            class_file = self.load_class_from_jar(classname)
        else:

            parts = classname.split('/')

            class_file = None
            for classpath in self.classpath:
                class_filename = os.path.join(*([classpath]+parts))+'.class'
                if os.path.isfile(class_filename):
                    class_file = open(class_filename)
                    break
            else:
                raise Exception('class file not found: %s' % classname)

        assert class_file is not None

        klass = ClassReader(classname, class_file).klass
        return klass
