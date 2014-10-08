import sys

MAGIC = [0xCA, 0xFE, 0xBA, 0xBE]

class MalformedClassException(Exception):
    pass

class ClassReader:
    def __init__(self, filereader):
        self.filereader = filereader
        self.parse()

    def parse(self):
        # read the first magic bytes
        for magic in MAGIC:
            byte = self._read_byte()
            if byte != magic:
                raise MalformedClassException()

        # class file version
        self.minor_version = self._read_byte2()
        self.major_version = self._read_byte2()

        constant_pool_length = self._read_byte2()
        for i in xrange(constant_pool_length):
            pass

    def _read_byte(self):
        return ord(self.filereader.read(1))

    def _read_byte2(self):
        return ord(self.filereader.read(1)) << 8 | ord(self.filereader.read(1))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'classreader.py <filename>.class'
        sys.exit(0)
    ClassReader(open(sys.argv[1]))
