internCache = {} # XXX: upper bound on size somehow
def intern(klass, vm, method, frame):
    string = frame.get_local(0)
    value = string._values['value']
    if value in internCache:
        return internCache[value]
    internCache[value] = string
    return string
