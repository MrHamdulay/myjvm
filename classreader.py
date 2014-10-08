import sys

from classconstants import *
from constantpool import ConstantPool

class MalformedClassException(Exception):
    pass

class ClassReader:
    constant_pool = None
    file_reader = None
    def __init__(self, filereader):
        self.constant_pool = ConstantPool()
        self.file_reader = filereader
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
        for i in xrange(constant_pool_length-1):
            self.constant_pool.add_pool(self.parse_constant_pool_item())

        field_length = self._read_byte2()
        fields = []
        for i in xrange(field_length):
            self.fields.append(self.parse_field())

    def parse_constant_pool_item(self):
        tag = self._read_byte()

        if tag in (CONSTANT_Class, CONSTANT_String):
            # index into constant pool of type UTF8 that references a class / array type
            name_index = self._read_byte2()
            return tag, name_index
        elif tag in (CONSTANT_Fieldref, CONSTANT_Methodref, CONSTANT_InterfaceMethodref):
            class_index = self._read_byte2()
            name_and_type_index = self._read_byte2()
            return tag, class_index, name_and_type_index
        elif tag == CONSTANT_Integer:
            integer = self._read_byte4()
            return tag, integer
        elif tag == CONSTANT_Float:
            bytes = self._read_byte4()
            if bytes == 0x7f800000:
                value = float('+inf')
            elif bytes == 0xff800000:
                value = float('-inf')
            elif 0x7f800001 <= bytes <= 0x7fffffff or 0xff800001 <= bytes <= 0xffffffff:
                value = float('nan')
            else:
                s = 1 if ((bits >> 31) == 0) else -1
                e = ((bits >> 23) & 0xff)
                m = ((bits & 0x7fffff) << 1) if e == 0 else (bits & 0x7fffff) | 0x800000
                value = s * e * m * float('2e-150')
            return tag, value
        elif tag == CONSTANT_Double:
            high_bytes = self._read_byte4()
            low_bytes = self._read_byte4()
            bytes = (high_bytes<<32)+low_bytes
            if bytes == 0x7ff0000000000000L:
                value = float('+inf')
            elif bytes == 0xfff0000000000000L:
                value = float('-inf')
            elif 0x7ff0000000000001L <= bytes <= 0x7fffffffffffffffL or 0xfff0000000000001L <= bytes <= 0xffffffffffffffffL:
                value = float('nan')
            else:
                s = 1 if ((bits >> 63) == 0) else -1
                e = ((bits >> 52) & 0x7ffL)
                m = ((bits & 0xfffffffffffffL) << 1) if e == 0 else (bits & 0xfffffffffffffL) | 0x10000000000000L
                value = s * e * m * float('2e-150')
            return tag, value
        elif tag == CONSTANT_Long:
            high_bytes = self._read_byte4()
            low_bytes = self._read_byte4()
            return tag, (high_bytes<<32) + low_bytes
        elif tag == CONSTANT_NameAndType:
            name_index = self._read_byte2()
            descriptor_index = self._read_byte2()
            return tag, name_index, descriptor_index
        elif tag == CONSTANT_Utf8:
            length = self._read_byte2()
            string = ''
            byte_index = 0
            while byte_index < length:
                codepoint = self._read_byte()
                byte_index += 1
                # just one byte
                if codepoint >> 7 == 0:
                    pass
                elif codepoint >> 6 == 6:
                    other_byte = self._read_byte()
                    byte_index += 1
                    assert other_byte >> 6 == 2
                    codepoint = ((codepoint & 0x1f) << 6) + (other_byte & 0x3f)
                elif codepoint >> 4 == 14:
                    y, z = self._read_byte(), self._read_byte()
                    assert y >> 6 == 2
                    assert z >> 6 == 2
                    byte_index += 2
                    codepoint = ((codepoint & 0xf) << 12) + ((y & 0x3f) << 6) + (z & 0x3f)
                # UTF-16
                elif codepoint == int('11101101', base=2):
                    v, w, x, y, z = self.read_byte()
                    codepoint += 5
                    assert (v >> 4) == int('1010', base=2)
                    assert (w >> 6) == 3
                    assert x == int('11101101', base=2)
                    assert (y >> 5) == int('1011', base=2)
                    codepoint = 0x10000 + ((v & 0x0f) << 16) + ((w & 0x3f) << 10) + ((y & 0x0f) << 6) + (z & 0x3f)

                string += unichr(codepoint)
            return tag, string
        elif tag == CONSTANT_MethodHandle:
            reference_handle = self._read_byte()
            reference_index = self._read_byte2()
            return tag, reference_handle, reference_index
        elif tag == CONSTANT_MethodType:
            descriptor_index = self._read_byte2()
            return tag, descriptor_index
        elif tag == CONSTANT_InvokeDynamic:
            bootstrap_method_attr_index = self._read_byte2()
            name_and_type_index = self._read_byte22()
            return tag, bootstrap_method_attr_index, name_and_type_index
        else:
            raise Exception('Unknown tag in constant pool ' + tag)

    def parse_field(self):
        access_flags = self._read_byte2()
        name_index = self._read_byte2()
        descriptor_index = self._read_byte2()
        attributes_count = self._read_byte2()
        attributes = []
        for i in xrange(attributes_count):
            attributes.append(self.parse_attribute())
        return access_flags, name_index, descriptor_index, attributes

    def parse_attribute(self):
        name_index = self._read_byte2()
        length = self._read_byte4()
        name = self.constant_pool.get_string(attribute_name_index)

        if name == 'ConstantValue':
            value_index = self._read_byte2()
            return name_index, length, value_index
        elif name == 'Code':
            max_stack = self._read_byte2()
            max_locals = self._read_byte2()
            code_length = self._read_byte4()
            code = [self._read_byte() for i in xrange(code_length)]
            exception_table_length = self._read_byte2()
            exceptions = []
            for i in xrange(exception_table_length):
                #start_pc, end_pc, handler_pc, catch_type
                handler = [self._read_byte2() for x in xrange(4)]
                exceptions.append(handler)

            attributes = []
            attribute_count = self._read_byte2()
            for i in xrange(attribute_count):
                attributes.append(self.parse_attribute())
            return name, max_stack, max_locals, code, exceptions, attributes
        elif name == 'StackMapTable':
            num_entries = self._read_byte2()
            stack_map_frames = []
            for i in xrange(num_entries):
                stack_map_frames.append(self.parse_stack_map_frame())
            return name, stack_map_frames
        else:
            print 'Unknown attribute', name
            for i in xrange(length):
                self._read_byte()
            return name,

    def parse_stack_map_frame(self):
        tag = self._read_byte()

        # SAME
        # frame has the same type
        if 0 <= tag <= 63:
            return 'SAME'
        elif 64 <= tag <= 127:
            verification_info = self.parse_verification_info()
            offset_delta = tag - 64
            return 'SAME_LOCALS_1_STACK_ITEM', offset_delta, verification_info
        elif tag == 247:
            offset_delta = self._read_byte2()
            verification_info = self.parse_verification_info()
            return 'SAME_LOCALS_1_STACK_ITEM_EXTENDED', offset_delta, verification_info
        elif 248 <= tag <= 250:
            offset_delta = 251 - tag
            return 'CHOP', offset_delta
        elif tag == 251:
            offset_delta = self._read_byte2()
            return 'SAME_FRAME_EXTENDED'
        elif 252 <= tag <= 254:
            offset_delta = self._read_byte2()
            verification_info = []
            for i in xrange(tag - 251):
                verification_info.append(self.parse_verification_info())
            return 'APPEND', offset_delta, verification_info()
        elif tag == 255:
            offset_delta = self._read_byte2()
            number_of_locals = self._read_byte2()
            locals_ = []
            for i in xrange(number_of_locals):
                locals_.append(self.parse_verification_info())
            number_of_stack_items = self._read_byte2()
            for i in xrange(number_of_stack_items):
                locals_.append(self.parse_verification_info())

    def parse_verification_info(self):
        tag = self._read_byte()
        if tag in (ITEM_Top, ITEM_Integer, ITEM_Float, ITEM_Null, ITEM_UnitialisedThis, ITEM_Long, ITEM_Double):
            return tag,
        elif tag in (ITEM_Object, ITEM_Unitialised):
            offset = self._read_byte2()
            return tag, offset


    def _read_byte(self):
        return ord(self.file_reader.read(1))

    def _read_byte2(self):
        return ord(self.file_reader.read(1)) << 8 | ord(self.file_reader.read(1))

    def _read_byte4(self):
        value = 0
        for i in xrange(4):
            value = value << 8 | ord(self.file_reader.read(1))
        return value

    @property
    def human_readable_constant_pool(self):
        result = ''
        for constant in self.constant_pool:
            result += CONSTANT_POOL_NAMES[constant[0]-1] + ' ' + ' '.join(map(str, constant[1:])) +'\n'
        return result

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'classreader.py <filename>.class'
        sys.exit(0)
    classreader = ClassReader(open(sys.argv[1]))
    print classreader.human_readable_constant_pool
