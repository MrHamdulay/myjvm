def get_attribute(o, name):
    for attribute in o.attributes:
        if attribute.__class__.__name__ in (name, name+'Attribute'):
            return attribute
    raise Exception('No such attribute %s on %s' % (name, o))
