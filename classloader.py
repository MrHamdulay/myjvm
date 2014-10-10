import klasses
class DefaultClassLoader:
    def __init__(self):
        self.classpath = ['.']
        pass

    def load(self, classname):
        parts = classname.split('.')

