import sys
import logging

from classconstants import *
from classtypes import *
from constantpool import ConstantPool, ConstantPoolItem
from klass import Class

class MalformedClassException(Exception):
    pass

class ClassReader:
    file_reader = None
    def __init__(self, classname, filereader):
        self.offset = 0
        self.classname = classname
        self.klass = Class(classname)
        self.file_reader = filereader
        self.parse()

    def parse(self):
        # read the first magic bytes
        for magic in MAGIC:
            byte = self._read_byte()
            if byte != magic:
                raise MalformedClassException()

        klass = self.klass

        # class file version
        klass.minor_version = self._read_byte2()
        klass.major_version = self._read_byte2()

        constant_pool_length = self._read_byte2()
        klass.constant_pool = ConstantPool(constant_pool_length)
        while klass.constant_pool.size < constant_pool_length-1:
            klass.constant_pool.add_pool(self.parse_constant_pool_item())

        klass.access_flags = self._read_byte2()
        klass.this_class = klass.constant_pool.get_class(self._read_byte2())
        super_class_index = self._read_byte2()
        klass.super_class = 'java/lang/Object'
        if super_class_index != 0:
            klass.super_class = klass.constant_pool.get_class(super_class_index)

        interfaces_count = self._read_byte2()
        for i in xrange(interfaces_count):
            klass.interfaces.append(klass.constant_pool.get_class(self._read_byte2()))


        field_length = self._read_byte2()
        for i in xrange(field_length):
            field = self.parse_field()
            klass.fields[field.name] = field

        method_count = self._read_byte2()
        for i in xrange(method_count):
            method = self.parse_method()
            klass.methods[Class.method_name(method)] = method

        klass.attributes = self.parse_attributes()

    def parse_constant_pool_item(self):
        tag = self._read_byte()

        if tag in (CONSTANT_Class, CONSTANT_String):
            # index into constant pool of type UTF8 that references a class / array type
            name_index = self._read_byte2()
            return ConstantPoolItem(tag, [name_index])
        elif tag in (CONSTANT_Fieldref, CONSTANT_Methodref, CONSTANT_InterfaceMethodref):
            class_index = self._read_byte2()
            name_and_type_index = self._read_byte2()
            return ConstantPoolItem(tag, [class_index, name_and_type_index])
        elif tag == CONSTANT_Integer:
            integer = self._read_byte4()
            return ConstantPoolItem(tag, [integer])
        elif tag == CONSTANT_Float:
            bytes = self._read_byte4()
            if bytes == 0x7f800000:
                value = float('+inf')
            elif bytes == 0xff800000:
                value = float('-inf')
            elif 0x7f800001 <= bytes <= 0x7fffffff or 0xff800001 <= bytes <= 0xffffffff:
                value = float('nan')
            else:
                s = 1 if ((bytes >> 31) == 0) else -1
                e = ((bytes >> 23) & 0xff)
                m = ((bytes & 0x7fffff) << 1) if e == 0 else (bytes & 0x7fffff) | 0x800000
                value = s * e * m * float('2e-150')
            return ConstantPoolItem(tag, [value])
        elif tag == CONSTANT_Double:
            high_bytes = self._read_byte4()
            low_bytes = self._read_byte4()
            if high_bytes == 0x7ff00000 and low_bytes == 0x00000000:
                value = float('+inf')
            elif high_bytes == 0xfff00000 and low_bytes == 00000000:
                value = float('-inf')
            elif (0x7ff00000 <= high_bytes <= 0x7fffffff) or (0xfff00000 <= high_bytes <= 0xffffffff):
                value = float('nan')
            else:
                bytes = (high_bytes<<32)+low_bytes
                s = 1 if ((bytes >> 63) == 0) else -1
                e = ((bytes >> 52) & 0x7ffL)
                m = ((bytes & 0xfffffffffffffL) << 1) if e == 0 else (bytes & 0xfffffffffffffL) | 0x10000000000000L
                value = s * e * m * float('2e-150')
            return ConstantPoolItem(tag, [value])
        elif tag == CONSTANT_Long:
            high_bytes = self._read_byte4()
            low_bytes = self._read_byte4()
            return ConstantPoolItem(tag, [(high_bytes<<32) + low_bytes])
        elif tag == CONSTANT_NameAndType:
            name_index = self._read_byte2()
            descriptor_index = self._read_byte2()
            return ConstantPoolItem(tag, [name_index, descriptor_index])
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
            return ConstantPoolItem(tag, [], [string])
        elif tag == CONSTANT_MethodHandle:
            reference_handle = self._read_byte()
            reference_index = self._read_byte2()
            return ConstantPoolItem(tag, [reference_handle, reference_index])
        elif tag == CONSTANT_MethodType:
            descriptor_index = self._read_byte2()
            return ConstantPoolItem(tag, [descriptor_index])
        elif tag == CONSTANT_InvokeDynamic:
            bootstrap_method_attr_index = self._read_byte2()
            name_and_type_index = self._read_byte22()
            return ConstantPoolItem(tag, [bootstrap_method_attr_index, name_and_type_index])

        raise Exception('Unknown tag in constant pool %s' % tag)

    def parse_field(self):
        access_flags = self._read_byte2()
        name_index = self._read_byte2()
        descriptor_index = self._read_byte2()
        attributes = self.parse_attributes()

        name = self.klass.constant_pool.get_string(name_index)
        descriptor = self.klass.constant_pool.get_string(descriptor_index)
        return Field(access_flags, name, descriptor, attributes)

    def parse_attributes(self):
        attributes = []
        attribute_count = self._read_byte2()
        for i in xrange(attribute_count):
            attributes.append(self.parse_attribute())
        return attributes


    def parse_attribute(self):
        name_index = self._read_byte2()
        # TODO: somehow assert we are reading exactly length bytes by the end of this
        attribute_length = self._read_byte4()
        start_offset = self.offset
        name = self.klass.constant_pool.get_string(name_index)

        attribute = None
        if name == 'ConstantValue':
            value_index = self._read_byte2()
            type, value, _ = self.klass.constant_pool.get_object(0, value_index)
            attribute = ConstantValueAttribute(value, type)
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

            attributes = self.parse_attributes()

            attribute = CodeAttribute(max_stack, max_locals, code, exceptions, attributes)
        elif name == 'StackMapTable':
            num_entries = self._read_byte2()
            stack_map_frames = []
            for i in xrange(num_entries):
                stack_map_frames.append(self.parse_stack_map_frame())
            attribute = StackMapTableAttribute(stack_map_frames)
        elif name == 'Exceptions':
            num_exceptions = self._read_byte2()
            exception_indexes = []
            for i in xrange(num_exceptions):
                exception_indexes.append(self._read_byte2())
            attribute = ExceptionsAttribute(exception_indexes)
        elif name == 'InnerClasses':
            num_classes = self._read_byte2()
            inner_classes = []
            for i in xrange(num_classes):
                inner_class_info_index = self._read_byte2()
                outer_class_info_index = self._read_byte2()
                inner_name_index = self._read_byte2()
                inner_class_access_flags = self._read_byte2()

                inner_class = self.klass.constant_pool.get_class_name(inner_class_info_index)
                outer_class = None # C is top level or an interface
                inner_name = None # C is an anonymous class
                if outer_class_info_index != 0:
                    outer_class = self.klass.constant_pool.get_class_name(outer_class_info_index)
                if inner_name_index != 0:
                    inner_name = self.klass.constant_pool.get_string(inner_name_index)
                inner_classes.append(InnerClass(inner_class, outer_class, inner_name, inner_class_access_flags))
            attribute = InnerClassesAttribute(inner_classes)
        elif name == 'EnclosingMethod':
            class_index = self._read_byte2()
            method_index = self._read_byte2()
            classs = self.klass.constant_pool.get_class(class_index)
            attribute = EnclosingMethodAttribute(classs, method_index)
        elif name == 'Synthetic':
            attribute = SyntheticAttribute()
        elif name == 'Signature':
            signature_index = self._read_byte2()
            attribute = SignatureAttribute(signature_index)
        elif name == 'SourceFile':
            source_file_index = self._read_byte2()
            source_file = self.klass.constant_pool.get_string(source_file_index)
            attribute = SourceFileAttribute(source_file)
        elif name == 'LineNumberTable':
            length = self._read_byte2()
            line_table = []
            for i in xrange(length):
                start_pc, line_number = self._read_byte2(), self._read_byte2()
                line_table.append((start_pc, line_number))
            attribute = LineNumberTableAttribute(line_table)
        elif name in ('RuntimeVisibleAnnotations', 'RuntimeInvisibleAnnotations'):
            num_annotations = self._read_byte2()
            annotations = []
            for i in xrange(num_annotations):
                annotations.append(self.parse_annotation())

            if name == 'RuntimeVisibleAnnotations':
                attribute = RuntimeVisibleAnnotations(annotations)
            elif name == 'RuntimeInvisibleAnnotations':
                attribute = RuntimeInvisibleAnnotations(annotations)
        elif name in ('RuntimeVisibleParameterAnnotations', 'RuntimeInvisibleParameterAnnotations'):
            num_parameters = self._read_byte()
            parameters = []
            for i in xrange(num_parameters):
                num_annotations = self._read_byte2()
                annotations = []
                for i in xrange(num_annotations):
                    annotations.append(self.parse_annotation())
                parameters.append(annotations)
            if name == 'RuntimeVisibleParameterAnnotations':
                attribute = RuntimeVisibleParameterAnnotations(parameters)
            else:
                attribute = RuntimeInvisibleParameterAnnotations(parameters)
        elif name in ('RuntimeVisibleTypeAnnotations', 'RuntimeInvisibleTypeAnnotations'):
            num_annotations = self._read_byte2()
            type_annotations = []
            for i in xrange(num_annotations):
                type_annotations.append(self.parse_type_annotation())
            if name == 'RuntimeVisibleTypeAnnotations':
                attribute = RuntimeVisibleTypeAnnotations(type_annotations)
            else:
                attribute = RuntimeInvisibleTypeAnnotations(type_annotations)
        elif name == 'AnnotationDefault':
            attribute_name_index = self._read_byte2()
            attribute_name_length = self._read_byte4()
            default_value = self.parse_element_value()

            attribute_name = self.klass.constant_pool.get_string(attribute_name_index)
            attribute = AnnotationDefaultAttribute(attribute_name, attribute_name_length, default_value)
        elif name == 'BootstapMethods':
            num_bootstrap_methods = self._read_byte2()
            bootstrap_methods = []
            for i in xrange(num_bootstrap_methods):
                bootstrap_method_ref = self._read_byte2()
                num_bootstrap_arguments = self._read_byte2()
                arguments = []
                for j in xrange(num_bootstrap_arguments):
                    arguments.append(self._read_byte2())
                bootstrap_methods.append(bootstrap_method_ref, arguments)
            attribute = BootstapMethodsAttribute(bootstrap_methods)
        elif name == 'MethodParameters':
            parameters_count = self._read_byte()
            parameters = []
            for i in xrange(parameters_count):
                name_index, access_flags = self._read_byte2(), self._read_byte2()
                name = self.klass.constant_pool.get_string(name_index)
                parameters.append((name, access_flags))
            attribute = MethodParametersAttribute(parameters)
        else:
            logging.debug('Unknown attribute %s' % name)
            for i in xrange(attribute_length):
                self._read_byte()
            attribute = name,

        end_offset = self.offset
        if attribute_length != end_offset - start_offset:
            raise Exception('Attribute parsing failure %s %d %d' % (name, attribute_length, end_offset - start_offset))
        return attribute

    def parse_annotation(self):
        type_index = self._read_byte2()
        element_values = self.parse_element_value_pairs()
        return type_index, element_values

    def parse_element_value_pairs(self):
        num_element_value_pairs = self._read_byte2()
        element_values = []
        for j in xrange(num_element_value_pairs):
            element_name_index = self.read_byte2()
            element_value = self.parse_element_value()
            element_name = self.klass.constant_pool.get_string(element_name_index)
            element_values.append((element_name, element_value))
        return 'element_value_pairs', element_values

    def parse_element_value(self):
        tag = chr(self._read_byte())
        if tag in 'BCDFIJSZsc':
            index = self._read_byte2()
            return tag, index
        elif tag == 'e':
            type_name_index = self._read_byte2()
            const_name_index = self._read_byte2()

            type_name = self.klass.constant_pool.get_string(type_name_index)
            const_name = self.klass.constant_pool.get_string(const_name_index)
            return tag, type_name, const_name
        elif tag == '@':
            annotation_value = self.parse_annotation()
            return tag, annotation_value
        elif tag == '[':
            num_values = self._read_byte2()
            array = []
            for i in xrange(num_values):
                array.append(self.parse_element_value())
            return tag, array


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
            chop = 251 - tag
            offset_delta = self._read_byte2()
            return 'CHOP', chop, offset_delta
        elif tag == 251:
            offset_delta = self._read_byte2()
            return 'SAME_FRAME_EXTENDED'
        elif 252 <= tag <= 254:
            offset_delta = self._read_byte2()
            verification_info = []
            for i in xrange(tag - 251):
                verification_info.append(self.parse_verification_info())
            return 'APPEND', offset_delta, verification_info
        elif tag == 255:
            offset_delta = self._read_byte2()
            number_of_locals = self._read_byte2()
            locals_ = []
            for i in xrange(number_of_locals):
                locals_.append(self.parse_verification_info())
            number_of_stack_items = self._read_byte2()
            for i in xrange(number_of_stack_items):
                locals_.append(self.parse_verification_info())
        else:
            raise Exception('Unknown stack map frame')

    def parse_verification_info(self):
        tag = self._read_byte()
        if tag in (ITEM_Top, ITEM_Integer, ITEM_Float, ITEM_Null, ITEM_UnitialisedThis, ITEM_Long, ITEM_Double):
            return tag,
        elif tag in (ITEM_Object, ITEM_Unitialised):
            offset = self._read_byte2()
            return tag, offset
        else:
            raise Exception('unknown verification type info')

    def parse_type_annotation(self):
        target_type = self.parse_target_type()
        type_path = self.parse_type_path()
        type_index = self._read_byte2()
        element_values = self.parse_element_value_pairs()
        return TypeAnnotation(target_type, type_path, type_index, element_values)

    def parse_target_type(self):
        target_type = self._read_byte()
        # type parameter target
        if taget_type in (0x0, 0x1):
            type_parameter_index = self._read_byte()
            return 'type', type_parameter_index
        # supertype target
        elif target_type == 0x10:
            supertype_index = self._read_byte2()
            return 'supertype', supertype_index
# type_parameter_bound_target
        elif target_type in (0x11, 0x12):
            type_parameter_index = self._read_byte()
            bound_index = self._read_byte()
            return 'type_parameter', type_parameter_index, bound_index
        # empty target_type
        elif target_type in (0x13, 0x14, 0x15):
            return 'empty',
# formal parameter target
        elif target_type == 0x16:
            formal_parameter_index = self._read_byte()
            return 'formal', formal_parameter_index
# throws target
        elif target_type == 0x17:
            throws_type_index = self._read_byte2()
            return 'throws', throws_type_index
#local var target
        elif target_type in (0x40, 0x41):
            length = self._read_byte2()
            local_var_table = []
            for i in xrange(length):
                start_pc = self._read_byte2()
                length = self._read_byte2()
                index = self._read_byte2()
                local_var_table.append((start_pc, length, index))
            return 'local_var', local_var_table
#catch target
        elif target_type == 0x42:
            exception_table_index = self._read_byte2()
            return 'catch', exception_table_index
#offset target
        elif target_type in (0x43, 0x44, 0x45, 0x46):
            offset = self._read_byte2()
            return 'offset', offset
        #type_argument_target
        elif target_type in (0x47, 0x48, 0x49, 0x4A, 0x4B):
            offset = self._read_byte2()
            type_argument_index = self._read_byte()
            return 'type_argument', offset, type_argument_index
        else:
            raise Exception

    def parse_type_path(self):
        path_length = self._read_byte()
        type_path  = []
        for i in xrange(path_length):
            type_path_kind = self._read_byte()
            type_argument_index = self._read_byte()
        return 'type_path', type_path

    def parse_method(self):
        access_flags = self._read_byte2()
        name_index = self._read_byte2()
        descriptor_index = self._read_byte2()

        descriptor = self.klass.constant_pool.get_string(descriptor_index)
        name = self.klass.constant_pool.get_string(name_index)
        attributes = self.parse_attributes()

        return Method(access_flags, name, descriptor, attributes)


    def _read_byte(self):
        self.offset +=1
        return ord(self.file_reader[self.offset-1])

    def _read_byte2(self):
        return (self._read_byte() << 8) | self._read_byte()

    def _read_byte4(self):
        value = 0
        for i in xrange(4):
            value = value << 8 | self._read_byte()
        return value

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'classreader.py <filename>.class'
        sys.exit(0)
    classreader = ClassReader(open(sys.argv[1]))
