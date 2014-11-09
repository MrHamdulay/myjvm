from classconstants import void, null

def fillInStackTrace(klass, vm, method, frame):
    return frame.get_local(0)
