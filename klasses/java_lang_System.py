from klass import NativeClass
from classtypes import Method
from classconstants import *

class out(NativeClass):
    def __init__(self):
        NativeClass.__init__(self)
        self.methods = {
                'println': Method(0, 'println', '(Ljava/lang/String;)V', [])
        }
    def println(self, string):
        print string

class System(NativeClass):
    out = out()
