def debug(*args):
    print 'Log: ', ', '.join(x.encode('utf-8') for x in args)
