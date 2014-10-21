import os.path
try:
    from rpython.rlib.rzipfile import RZipFile
    ZipFile = RZipFile
except:
    RZipFile = None
    from zipfile import ZipFile

from classreader import ClassReader

class DefaultClassLoader:
    def __init__(self, classpath):
        self.classpath = classpath
        print classpath
        self.lazy_classes = {}

    def load_jar(self, jarfilename):
        jar = ZipFile(jarfilename)
        for zipinfo in jar.filelist:
            classname = zipinfo.filename
            if not classname.endswith('.class'):
                continue
            self.lazy_classes[classname.split('.class')[0]] = jar

    def load_class_from_jar(self, classname):
        if RZipFile:
            return self.lazy_classes[classname].read(classname+'.class')
        else:
            return self.lazy_classes[classname].open(classname+'.class').read()


    def load(self, classname):
        class_file = None

        if classname in self.lazy_classes:
            class_file = self.load_class_from_jar(classname)
        else:

            parts = classname.split('/')

            class_file = None
            for classpath in self.classpath:
                class_filename = '%s/%s.class' % (classpath, classname)
                if os.path.isfile(class_filename):
                    class_file = open(class_filename).read()
                    break
            else:
                raise Exception('class file not found: %s' % classname)

        assert class_file is not None

        klass = ClassReader(classname, class_file).klass
        return klass
