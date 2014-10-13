from klass import NativeClass
from classtypes import Method
from classconstants import *

class PrintStream(NativeClass):
    def __init__(self):
        NativeClass.__init__(self)
        self.methods = {
                'println': Method(0, 'println', '(Ljava/lang/String;)V', [])
        }
    def println(self, inst, arg):
        print inst, arg
        raise Exception
