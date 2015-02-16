from __future__ import absolute_import
from klass import ArrayInstance

class NoSuchAttributeError(Exception):
    pass

def get_attribute(o, name):
    if not hasattr(o, 'attributes'):
        raise NoSuchAttributeError('No such attribute %s on %s' % (name, o))
    for attribute in o.attributes:
        if attribute.__class__.__name__ in (name, name+'Attribute'):
            return attribute
    raise NoSuchAttributeError('No such attribute %s on %s' % (name, o))

def make_string(vm, value):
    string = vm.load_class('java/lang/String').instantiate()
    string._values['value'] = ArrayInstance(vm.load_class('char'), len(value))
    string._values['value'].array = map(ord, value)
    string._values['count'] = len(value)
    return string

def to_python_string(string):
    return ''.join(map(unichr, string._values['value'].array))
