from __future__ import absolute_import
from classconstants import void, null, ACC_PUBLIC
from utils import make_string

def getCallerClass(klass, vm, method, frame):
    return vm.frame_stack[-2].klass.java_instance

def getClassAccessFlags(klass, vm, method, frame):
    # XXX: implement properly, not sure what the rule is
    return ACC_PUBLIC
    #klass = frame.get_local(0)
    #return vm.load_class(klass._values['class_name']).access_flags
