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

        if classname in self.lazy_classes:
            classname = self.load_class_from_jar(classname)

        if isinstance(classname, basestring):
            parts = classname.split('/')

            class_file = None
            for classpath in self.classpath:
                class_filename = os.path.join(*([classpath]+parts))+'.class'
                if os.path.isfile(class_filename):
                    class_file = open(class_filename)
                    break
            else:
                raise Exception('class file not found: %s' % classname)
        elif hasattr(classname, 'read'):
            # assume that this is a file object type
            class_file = classname
        else:
            raise Exception

        klass = ClassReader(classname, class_file).klass
        return klass
