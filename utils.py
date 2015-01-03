class NoSuchAttributeError(Exception):
    pass

def get_attribute(o, name):
    if not hasattr(o, 'attributes'):
        raise NoSuchAttributeError('No such attribute %s on %s' % (name, o))
    for attribute in o.attributes:
        if attribute.__class__.__name__ in (name, name+'Attribute'):
            return attribute
    raise NoSuchAttributeError('No such attribute %s on %s' % (name, o))
