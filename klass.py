from constantpool import ConstantPool

class Class:
    major_version = None
    minor_version = None

    constant_pool = None
    access_flags = None
    this_class = None
    super_class = None

    interfaces = None
    fields = None
    methods = None
    attributes = None

    def __init__(self):
        self.constant_pool = ConstantPool()
        self.interfaces = []
        self.fields = []
        self.methods = []
        self.attributes = []

