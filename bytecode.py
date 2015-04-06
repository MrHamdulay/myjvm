from __future__ import absolute_import
import operator
import logging
import struct
import math

bytecodes = {}

from rpython.rlib.rarithmetic import longlongmask

from classconstants import *
from klass import Class, ClassInstance, ArrayInstance, ArrayClass
from descriptor import parse_descriptor, descriptor_is_array
from arithmetic import *

def default_value(descriptor):
    if descriptor[0] in '[L':
        return null
    return 0

def register_bytecode(start, end=-1, use_next=0, bc_repr=None):
    def decorator(f):
        if decorator.end == -1:
            decorator.end = decorator.start
        for i in xrange(decorator.start, decorator.end+1):
            assert i not in bytecodes
            bytecodes[i] = (decorator.start, f, use_next, bc_repr)
        return f
    decorator.start = start
    decorator.end = end
    return decorator

def decode_signed_offset(bytecode, pc):
    jump = struct.unpack('>h', chr(bytecode[pc+1])+chr(bytecode[pc+2]))[0]+pc
    return jump

def decode_signed_int(bytecode, pc):
    return struct.unpack('>i', ''.join(map(chr, bytecode[pc:pc+4])))[0]

@register_bytecode(1)
def aconst_null(vm, frame, offset, bytecode):
    frame.push(null)

def iconst_n_repr(vm, frame, index, offset, bytecode):
    return str(offset-1)

@register_bytecode(2, 8, bc_repr=iconst_n_repr)
def iconst_n(vm, frame, offset, bytecode):
    frame.push(offset-1)

@register_bytecode(9, 10)
def lconst_n(vm, frame, offset, bytecode):
    frame.push(offset)

@register_bytecode(11, 13)
def fconst_n(vm, frame, offset, bytecode):
    frame.push(float(offset))

@register_bytecode(14, 15)
def dconst_n(vm, frame, offset, bytecode):
    frame.push(float(offset))

@register_bytecode(16, use_next=1)
def bipush(vm, frame, offset, bytecode):
    frame.push(bytemask(bytecode[frame.pc+1]))
    frame.pc = frame.pc+1

@register_bytecode(17, use_next=2)
def sipush(vm, frame, offset, bytecode):
    frame.push((bytecode[frame.pc+1]<<8) | bytecode[frame.pc+2])
    frame.pc = frame.pc+2

def ldc_repr(vm, frame, index, offset, bytecode):
    constant_pool_index = bytecode[index+1]
    return unicode(vm.resolve_field(frame.klass, constant_pool_index))

@register_bytecode(18, use_next=1, bc_repr=ldc_repr)
def ldc(vm, frame, offset, bytecode):
    constant_pool_index = bytecode[frame.pc+1]
    field = vm.resolve_field(frame.klass, constant_pool_index)
    frame.push(field)
    frame.pc = frame.pc+1

def ldcw_repr(vm, frame, index, offset, bytecode):
    constant_pool_index = (bytecode[index+1] << 8) +  bytecode[index+2]
    return unicode(vm.resolve_field(frame.klass, constant_pool_index))

@register_bytecode(19, use_next=2, bc_repr=ldcw_repr)
def ldc_w(vm, frame, offset, bytecode):
    constant_pool_index = (bytecode[frame.pc+1] << 8) +  bytecode[frame.pc+2]
    field = vm.resolve_field(frame.klass, constant_pool_index)
    frame.push(field)
    frame.pc = frame.pc+2

def ldc2_repr(vm, frame, index, offset, bytecode):
    index = (bytecode[index+1] << 8) +  bytecode[index+2]
    field = frame.klass.constant_pool.get_object(
            (CONSTANT_Double, CONSTANT_Long), index)[0][0]
    return unicode(field)

@register_bytecode(20, use_next=2, bc_repr=ldc2_repr)
def ldc2_w(vm, frame, offset, bytecode):
    index = (bytecode[frame.pc+1] << 8) +  bytecode[frame.pc+2]
    field = frame.klass.constant_pool.get_object(
            (CONSTANT_Double, CONSTANT_Long), index)[0][0]
    assert isinstance(field, (float, int, long)), 'incorrect type %s' % unicode(field)
    frame.push(field)
    frame.pc = frame.pc+2

def lstore_repr(vm, frame, index, offset, bytecode):
    return 'local[%d]' % bytecode[index+1]

@register_bytecode(21, use_next=1, bc_repr=lstore_repr) #iload
@register_bytecode(22, use_next=1, bc_repr=lstore_repr) #lload
@register_bytecode(25, use_next=1, bc_repr=lstore_repr) #aload
def iload(vm, frame, offset, bytecode):
    local = frame.get_local(bytecode[frame.pc+1])
    if bytecode[frame.pc] in (21, 22):
        assert isinstance(local, (long, int))
    elif bytecode[frame.pc] == 25:
        assert isinstance(local, (ClassInstance, ArrayClass)) or local is null, 'unexpected type %s' % type(local)
    else:
        raise Exception
    frame.push(local)
    frame.pc = frame.pc+1

def iload_n_repr(vm, frame, index, offset, bytecode):
    return unicode(offset)

@register_bytecode(26, 29, bc_repr=iload_n_repr)
def iload_n(vm, frame, offset, bytecode):
    local = frame.get_local(offset)
    frame.push(intmask(local))

@register_bytecode(30, 33, bc_repr=iload_n_repr)
def lload_n(vm, frame, offset, bytecode):
    local = frame.get_local(offset)
    frame.push(longlongmask(local))

@register_bytecode(34, 37)
def fload(vm, frame, offset, bytecode):
    local = frame.get_local(offset)
    assert isinstance(local, float)
    frame.push(local)

@register_bytecode(38, 41)
def dloat_n(vm, frame, offset, bytecode):
    frame.push(float(offset))

@register_bytecode(42, 45)
def aload_n(vm, frame, offset, bytecode):
    val = frame.local_variables[offset]
    assert isinstance(val, (ClassInstance, ArrayClass)) or val is null
    frame.push(val)

@register_bytecode(46) #iaload
@register_bytecode(47) #laload
def iaload(vm, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    assert index >= 0 and index < len(array), '%d %s' % (index, array)
    frame.push(array.array[index])

@register_bytecode(50)
def aaload(vm, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    frame.push(array.array[index])

@register_bytecode(51)
def baload(vm, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    assert 0 <= index < len(array)
    frame.push(bytemask(array.array[index]))

@register_bytecode(52)
def caload(vm, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    if array is null:
        vm.throw_exception(frame, 'java/lang/NullPointerException')
    elif index < 0 or index >= len(array):
        vm.throw_exception(frame, 'java/lang/ArrayIndexOutOfBoundsException')
    else:
        frame.push(charmask(array.array[index]))

@register_bytecode(54, use_next=1, bc_repr=lstore_repr) #istore
@register_bytecode(55, use_next=1, bc_repr=lstore_repr) #lstore
@register_bytecode(58, use_next=1, bc_repr=lstore_repr) #astore
def lstore(vm, frame, offset, bytecode):
    index = bytecode[frame.pc+1]
    local = frame.pop()
    if bytecode[frame.pc] in (54, 55):
        assert isinstance(local, (int, long))
    elif bytecode[frame.pc] == 58:
        assert isinstance(local, (ClassInstance, ArrayClass)) or local is null
    frame.insert_local(index, local)
    frame.pc = frame.pc + 1

def istore_n_repr(vm, frame, index, offset, bytecode):
    return unicode(offset)

@register_bytecode(59, 62, bc_repr=istore_n_repr)
def istore_n(vm, frame, offset, bytecode):
    local = frame.pop()
    frame.insert_local(offset, intmask(local))

@register_bytecode(63, 66, bc_repr=istore_n_repr)
def lstore_n(vm, frame, offset, bytecode):
    local = frame.pop()
    frame.insert_local(offset, longlongmask(local))

@register_bytecode(67, 70)
def fstore_n(vm, frame, offset, bytecode):
    frame.insert_local(offset, float(frame.pop()))

@register_bytecode(71, 74)
def dstore_n(vm, frame, offset, bytecode):
    frame.insert_local(offset, float(frame.pop()))

@register_bytecode(75, 78)
def astore(vm, frame, offset, bytecode):
    reference = frame.pop()
    assert isinstance(reference, (ArrayClass, ClassInstance)) or reference is null
    frame.insert_local(offset, reference)

@register_bytecode(79)
def iastore(vm, frame, offset, bytecode):
    value, index, array = intmask(frame.pop()), frame.pop(), frame.pop()
    assert array is not null
    assert index >= 0 and index < len(array)
    array.array[index] = value

@register_bytecode(83)
def aastore(vm, frame, offset, bytecode):
    value, index, arrayref = frame.pop(), frame.pop(), frame.pop()
    assert arrayref is not null
    assert index >= 0 and index < len(arrayref.array)
    arrayref.array[index] = value

@register_bytecode(84)
def bastore(vm, frame, offset, bytecode):
    value, index, arrayref = frame.pop(), frame.pop(), frame.pop()
    assert arrayref is not null
    assert index >= 0 and index < len(arrayref.array)
    arrayref.array[index] = value

@register_bytecode(85)
def castore(vm, frame, offset, bytecode):
    value, index, arrayref = frame.pop(), frame.pop(), frame.pop()
    assert arrayref is not null
    assert index >= 0 and index < len(arrayref.array)
    arrayref.array[index] = charmask(value)

@register_bytecode(87)
def pop(vm, frame, offset, bytecode):
    frame.pop()

@register_bytecode(88)
def pop2(vm, frame, offset, bytecode):
    frame.pop()
    frame.pop()


@register_bytecode(89)
def dup(vm, frame, offset, bytecode):
    frame.push(frame.stack[-1])

@register_bytecode(90)
def dupx1(vm, frame, offset, bytecode):
    value1 = frame.pop()
    value2 = frame.pop()
    frame.push(value1)
    frame.push(value2)
    frame.push(value1)

@register_bytecode(96)
def iadd(vm, frame, offset, bytecode):
    frame.push(intmask(intmask(frame.pop())+intmask(frame.pop())))

@register_bytecode(97)
def ladd(vm, frame, offset, bytecode):
    frame.push(longlongmask(longlongmask(frame.pop())+longlongmask(frame.pop())))

@register_bytecode(100)
def isub(vm, frame, offset, bytecode):
    a, b = intmask(frame.pop()), intmask(frame.pop())
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(b-a))

@register_bytecode(104)
def imul(vm, frame, offset, bytecode):
    a, b = intmask(frame.pop()), intmask(frame.pop())
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(a*b))

@register_bytecode(105)
def lmul(vm, frame, offset, bytecode):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, (int, long)) and isinstance(b, (int, long))
    frame.push(longlongmask(a*b))

@register_bytecode(106)
def fmul(vm, frame, offset, bytecode):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, float) and isinstance(b, float)
    frame.push(a*b)

@register_bytecode(108)
def idiv(vm, frame, offset, bytecode):
    b, a = frame.pop(), frame.pop()
    frame.push(intmask(a)/intmask(b))

@register_bytecode(109)
def ldiv(vm, frame, offset, bytecode):
    b, a = frame.pop(), frame.pop()
    frame.push(longlongmask(a)/longlongmask(b))

@register_bytecode(110)
def fdiv(vm, frame, offset, bytecode):
    b, a = frame.pop(), frame.pop()
    frame.push(float(a)/float(b))

@register_bytecode(111)
def ddiv(vm, frame, offset, bytecode):
    b, a = frame.pop(), frame.pop()
    frame.push(float(a)/float(b))

@register_bytecode(122)
def ishr(vm, frame, offset, bytecode):
    b, a = frame.pop(), frame.pop()
    s = b & 0x1f
    print a, b, s
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(a>>s))

@register_bytecode(126)
def iand(vm, frame, offset, bytecode):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(a&b))

@register_bytecode(127)
def land(vm, frame, offset, bytecode):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, (long, int)) and isinstance(b, (long, int)), 'Mismatched type "%s", "%s"' % (a, b)
    frame.push(longlongmask(a&b))

@register_bytecode(132, use_next=2)
def iinc(vm, frame, offset, bytecode):
    index, raw_const = bytecode[frame.pc+1], bytecode[frame.pc+2]
    start_value = frame.get_local(index)
    const = struct.unpack('>b', chr(raw_const))[0]
    frame.insert_local(index, intmask(start_value + const))
    assert isinstance(start_value, int)
    frame.pc = frame.pc + 2

def zero_comparison(name, operator):
    def comparison(vm, frame, offset, bytecode):
        a=frame.pop()
        assert isinstance(a, int)
        if operator(a, 0):
            frame.pc = decode_signed_offset(bytecode, frame.pc)-1
            return
        frame.pc = frame.pc+2
    comparison.__name__ = name
    return comparison

ifeq = register_bytecode(153, use_next=2)(zero_comparison('ifeq', operator.eq))
ifne = register_bytecode(154, use_next=2)(zero_comparison('ifne', operator.ne))
iflt = register_bytecode(155, use_next=2)(zero_comparison('iflt', operator.lt))
ifge = register_bytecode(156, use_next=2)(zero_comparison('ifge', operator.ge))
ifgt = register_bytecode(157, use_next=2)(zero_comparison('ifgt', operator.gt))
ifle = register_bytecode(158, use_next=2)(zero_comparison('ifle', operator.le))

def integer_comparison(name, operator):
    def comparison(vm, frame, offset, bytecode):
        b, a = frame.pop(), frame.pop()
        assert isinstance(a, int) and isinstance(b, int)
        if operator(a, b):
            print 'pass'
            frame.pc = decode_signed_offset(bytecode, frame.pc)-1
            return
        frame.pc = frame.pc+2
    comparison.__name__ = name
    return comparison

def cmp_repr(vm, frame, index, offset, bytecode):
    return str(decode_signed_offset(bytecode, index)-1)

if_cmpeq = register_bytecode(159, use_next=2, bc_repr=cmp_repr)(
        integer_comparison('if_cmpeq', operator.eq))
if_cmpne = register_bytecode(160, use_next=2, bc_repr=cmp_repr)(
        integer_comparison('if_cmpne', operator.ne))
if_cmplt = register_bytecode(161, use_next=2, bc_repr=cmp_repr)(
        integer_comparison('if_cmplt', operator.lt))
if_cmpge = register_bytecode(162, use_next=2, bc_repr=cmp_repr)(
        integer_comparison('if_cmpge', operator.ge))
if_cmpgt = register_bytecode(163, use_next=2, bc_repr=cmp_repr)(
        integer_comparison('if_cmpgt', operator.gt))
if_cmple = register_bytecode(164, use_next=2, bc_repr=cmp_repr)(
        integer_comparison('if_cmple', operator.le))

@register_bytecode(120) #ishl
def ishl(vm, frame, offset, bytecode):
    shift, value = frame.pop(), intmask(frame.pop())
    assert 0 <= shift <= 31
    frame.push(intmask(value << shift))

@register_bytecode(121) #lshl
def lshl(vm, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 63
    frame.push(longlongmask(long(value) << shift))

@register_bytecode(124) #iushr
def iushr(vm, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    shift &= 0x1f
    assert 0 <= shift <= 31
    assert isinstance(value, int)
    unsigned = struct.unpack('>I', struct.pack('>i', value))[0]
    unsigned >>= shift
    frame.push(struct.unpack('>i', struct.pack('>I', unsigned))[0])

@register_bytecode(125) #lushr
def lushr(vm, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 63
    frame.push(longlongmask(value >> shift))

@register_bytecode(128) #ior
def ior(vm, frame, offset, bytecode):
    val1, val2 = intmask(frame.pop()), intmask(frame.pop())
    frame.push(intmask(val1 | val2))

@register_bytecode(129) #lor
def lor(vm, frame, offset, bytecode):
    val1, val2 = frame.pop(), frame.pop()
    frame.push(longlongmask(val1 | val2))

@register_bytecode(130)
def ixor(vm, frame, offset, bytecode):
    val1, val2 = frame.pop(), frame.pop()
    frame.push(intmask(val1 ^ val2))

@register_bytecode(131)
def lxor(vm, frame, offset, bytecode):
    val1, val2 = frame.pop(), frame.pop()
    frame.push(longlongmask(val1 ^ val2))

@register_bytecode(133) # i2l
@register_bytecode(136) # l2i
def i2l(vm, frame, offset, bytecode):
    pass

@register_bytecode(134)
def i2f(vm, frame, offset, bytecode):
    frame.push(float(frame.pop()))

@register_bytecode(138)
def l2d(vm, frame, offset, bytecode):
    frame.push(frame.pop())

@register_bytecode(139)
def f2i(vm, frame, offset, bytecode):
    frame.push(int(frame.pop()))

@register_bytecode(145)
def i2b(vm, frame, offset, bytecode):
    frame.push(bytemask(frame.pop()))

@register_bytecode(146)
def i2c(vm, frame, offset, bytecode):
    v = frame.pop()
    frame.push(charmask(v))

@register_bytecode(148)
def lcmp(vm, frame, offset, bytecode):
    v1, v2 = frame.pop(), frame.pop()
    assert isinstance(v1, (long, int))
    assert isinstance(v2, (long, int))
    frame.push(cmp(v1, v2))

@register_bytecode(149)
def fcmpl(vm, frame, offset, bytecode):
    v2, v1 = frame.pop(), frame.pop()
    if math.isnan(v2) or math.isnan(v1):
        frame.push(-1)
        return
    assert isinstance(v1, float)
    assert isinstance(v2, float)
    frame.push(cmp(v1, v2))

@register_bytecode(150)
def fcmpl(vm, frame, offset, bytecode):
    v2, v1 = frame.pop(), frame.pop()
    if math.isnan(v2) or math.isnan(v1):
        frame.push(1)
        return
    assert isinstance(v1, float)
    assert isinstance(v2, float)
    frame.push(cmp(v1, v2))

@register_bytecode(165, use_next=2)
def if_acmpeq(vm, frame, offset, bytecode):
    if frame.pop() is frame.pop():
        frame.pc = decode_signed_offset(bytecode, frame.pc)-1
    else:
        frame.pc += 2

@register_bytecode(166, use_next=2)
def if_acmpne(vm, frame, offset, bytecode):
    if frame.pop() is not frame.pop():
        frame.pc = decode_signed_offset(bytecode, frame.pc)-1
    else:
        frame.pc += 2

def goto_repr(vm, frame, index, offset, bytecode):
    return str(decode_signed_offset(bytecode, index))

@register_bytecode(167, use_next=2, bc_repr=goto_repr)
def goto(vm, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc)-1
    assert frame.pc >= 0 and frame.pc < len(bytecode)

@register_bytecode(171, use_next=None)
def lookupswitch(vm, frame, offset, bytecode):
    add = 4 - ((frame.pc + 1) % 4)
    index = frame.pc + 1
    if add != 4:
        index += add
    assert index % 4 == 0
    default = decode_signed_int(bytecode, index)
    index += 4
    npairs = decode_signed_int(bytecode, index)
    index += 4
    key = frame.pop()
    # XXX: use a binary search
    for i in xrange(index, index+8*npairs, 8):
         match = decode_signed_int(bytecode, i)
         if match == key:
             frame.pc += decode_signed_int(bytecode, i+4) -1
             return True
    frame.pc += default - 1

@register_bytecode(172)
def ireturn(vm, frame, offset, bytecode):
    return_value = int(frame.pop())
    #assert not len(frame.stack)
    frame.return_value = intmask(return_value)

@register_bytecode(173)
def lreturn(vm, frame, offset, bytecode):
    return_value = long(frame.pop())
    #assert not len(frame.stack)
    frame.return_value = longlongmask(return_value)

@register_bytecode(174)
def freturn(vm, frame, offset, bytecode):
    return_value = float(frame.pop())
    #assert not len(frame.stack)
    frame.return_value = float(return_value)

@register_bytecode(175)
def dreturn(vm, frame, offset, bytecode):
    return_value = float(frame.pop())
    #assert not len(frame.stack)
    frame.return_value = float(return_value)

@register_bytecode(176)
def areturn(vm, frame, offset, bytecode):
    return_value = frame.pop()
    assert isinstance(return_value, ClassInstance) or return_value is null
    assert not len(frame.stack)
    frame.return_value = return_value

@register_bytecode(177)
def return_(vm, frame, offset, bytecode):
    assert not frame.stack
    frame.return_value = void

def getstatic_repr(vm, frame, index, offset, bytecode):
    ref_index = (bytecode[index+1]<<8) | (bytecode[index+2])
    return ' '.join(map(unicode, vm.resolve_field(frame.klass, ref_index)))

@register_bytecode(178, use_next=2, bc_repr=getstatic_repr)
def getstatic(vm, frame, offset, bytecode):
    ref_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(
            frame.klass, ref_index)
    if field_name in field_klass.field_overrides:
        frame.push(field_klass.field_overrides[field_name])
    elif field_name in field_klass.field_values:
        frame.push(field_klass.field_values[field_name])
    else:
        frame.push(default_value(field_descriptor))
    frame.pc = frame.pc + 2

@register_bytecode(179, use_next=2, bc_repr=getstatic_repr)
def putstatic(vm, frame, offset, bytecode):
    ref_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(frame.klass, ref_index)
    value = frame.pop()
    assert field_name in field_klass.fields
    field_klass.field_values[field_name] = value
    frame.pc = frame.pc + 2

@register_bytecode(180, use_next=2, bc_repr=getstatic_repr)
def getfield(vm, frame, offset, bytecode):
    field_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(
            frame.klass, field_index, 'Fieldref')
    objectref = frame.pop()
    if objectref is null:
        vm.throw_exception(frame, 'java/lang/NullPointerException')
    else:
        assert isinstance(objectref, ClassInstance)
        if field_name not in objectref._values:
            value = default_value(objectref._klass.get_field(field_name).descriptor)
        else:
            value = objectref._values[field_name]
        frame.push(value)
    frame.pc = frame.pc + 2


@register_bytecode(181, use_next=2, bc_repr=getstatic_repr)
def putfield(vm, frame, offset, bytecode):
    field_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(
            frame.klass, field_index, 'Fieldref')
    value, objectref = frame.pop(), frame.pop()
    assert isinstance(objectref, ClassInstance) or objectref is null
    objectref._values[field_name] = value
    frame.pc = frame.pc + 2

def invokevirtual_repr(vm, frame, index, offset, bytecode):
    return ''
    ref_index = vm.constant_pool_index(bytecode, index)
    new_klass, method = vm.resolve_field(frame.klass, ref_index)
    return '%s.%s %s' % (new_klass.name, method.name, method.descriptor)

@register_bytecode(182, use_next=2, bc_repr=invokevirtual_repr)
@register_bytecode(183, use_next=2, bc_repr=invokevirtual_repr)
@register_bytecode(184, use_next=2, bc_repr=invokevirtual_repr)
def invokevirtual_special(vm, frame, offset, bytecode):
    method_index = vm.constant_pool_index(bytecode, frame.pc)
    new_klass, method = vm.resolve_field(frame.klass, method_index)
    # fetch the instance and then extract the class from that.
    # we do this so that in the case of an abstract class we get
    # the implemented method
    if bytecode[frame.pc] == 182:
        instance = frame.stack[-len(method.parameters)-1]
        if instance is null:
            # remove all our method parameters
            for i in xrange(len(method.parameters)+1):
                frame.pop()
            raise Exception
            vm.throw_exception(frame, 'java/lang/NullPointerException')
            return
        assert new_klass.is_subclass(instance),\
            '%s not a subclass of %s' % (str(new_klass), str(instance))
        new_klass = instance._klass
    if bytecode[frame.pc] == 184:
        assert (method.access_flags & ACC_STATIC) != 0

    # find the superclass that contains this method (or we have it)
    method_name = Class.method_name(method.name, method.descriptor)
    while method_name not in new_klass.methods:
        new_klass = new_klass.super_class
        if new_klass.super_class == new_klass:
            break
    assert method_name in new_klass.methods

    new_method = new_klass.methods[method_name]
    vm.run_method(new_klass, new_method)
    frame.pc += 2

def invokeinterface_repr(vm, frame, index, offset, bytecode):
    ref_index = (bytecode[index+1]<<8) | (bytecode[index+2])
    klass, method = vm.resolve_field(frame.klass, ref_index)
    return '%s.%s' % (klass.name, method.name)

@register_bytecode(185, use_next=4, bc_repr=invokeinterface_repr)
def invokeinterface(vm, frame, offset, bytecode):
    method_index = vm.constant_pool_index(bytecode, frame.pc)
    new_klass, interface_method = vm.resolve_field(frame.klass, method_index)
    count, zero = bytecode[frame.pc+3], bytecode[frame.pc+4]
    assert zero == 0
    objectref = frame.stack[len(frame.stack)-count]
    assert objectref is not null

    klass, method = objectref._klass.get_method(
            interface_method.name,
            interface_method.descriptor)
    vm.run_method(klass, method)
    frame.pc += 4

@register_bytecode(187, use_next=2)
def new(vm, frame, offset, bytecode):
    klass_index = vm.constant_pool_index(bytecode, frame.pc)
    klass_name = frame.klass.constant_pool.get_class(klass_index)
    klass = vm.load_class(klass_name)
    instance = klass.instantiate()
    frame.push(instance)
    frame.pc = frame.pc  + 2

atypes = {4: 'boolean', 5: 'char', 6: 'float', 7: 'double', 8: 'byte', 9: 'short', 10: 'int', 11: 'long'}
@register_bytecode(188, use_next=1)
def newarray(vm, frame, offset, bytecode):
    atype = bytecode[frame.pc+1]

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    array = ArrayInstance(vm.load_class(atypes[atype]), size)
    frame.push(array)
    frame.pc = frame.pc + 1

@register_bytecode(189, use_next=2)
def anewarray(vm, frame, offset, bytecode):
    klass_name = frame.klass.constant_pool.get_class(
            vm.constant_pool_index(bytecode, frame.pc))
    klass = vm.load_class(klass_name)

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    frame.push(ArrayClass(klass, size))
    frame.pc = frame.pc + 2

@register_bytecode(190)
def arraylength(vm, frame, offset, bytecode):
    arrayref = frame.pop()
    print arrayref
    assert isinstance(arrayref, ArrayClass)
    frame.push(arrayref.size)

@register_bytecode(191)
def athrow(vm, frame, offset, bytecode):
    frame.raised_exception = frame.pop()

def _checkcast(vm, frame, reference, descriptor):
    if not isinstance(reference, ArrayClass):
        klass_name = descriptor
        klass = vm.load_class(klass_name)
        if klass.is_interface:
            return reference._klass.implements(klass)
        if isinstance(reference, ClassInstance):
            return klass.is_subclass(reference)
    elif reference._klass.is_interface:
        klass = vm.load_class(descriptor[1:])
        if not klass.name == 'java/lang/Object':
            return False
        return reference._klass.implements(klass)
    # this is an array type
    else:
        # if not array type must be java/lang/Object
        if not descriptor_is_array(descriptor):
            return descriptor == 'java/lang/Object'

        klass = vm.load_class(descriptor[1:])
        if klass.is_interface:
            return reference._klass.implements(klass)

        # array types match
        if reference._klass.name == descriptor[1:]:
            return True

        # recursively check types
        return _checkcast(
                vm,
                frame,
                reference._klass.instantiate(),
                descriptor[1:])

@register_bytecode(192, use_next=2)
def checkcast(vm, frame, offset, bytecode):
    reference = frame.pop() # S
    frame.pc += 2
    if reference is null:
        frame.push(reference)
        return
    descriptor = frame.klass.constant_pool.get_class(
        vm.constant_pool_index(bytecode, frame.pc-2))
    print descriptor
    if descriptor[0] == '[':
        descriptor = parse_descriptor(descriptor)[0]

    if _checkcast(vm, frame, reference, descriptor):
        frame.push(reference)
    else:
        vm.throw_exception(frame, 'java/lang/ClassCastException')


@register_bytecode(193, use_next=2)
def instanceof(vm, frame, offset, bytecode):
    objectref = frame.pop()
    frame.pc += 2
    if objectref is null:
        frame.push(0)
        return
    klass = vm.load_class(frame.klass.constant_pool.get_class(
        vm.constant_pool_index(bytecode, frame.pc-2)))
    frame.push(1 if klass.is_subclass(objectref) else 0)


@register_bytecode(198, use_next=2)
def ifnull(vm, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc)-1 if frame.pop() is null else frame.pc+2

@register_bytecode(199, use_next=2)
def ifnonnull(vm, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc)-1 if frame.pop() is not null else frame.pc+2

@register_bytecode(194)
def monitorenter(vm, frame, offset, bytecode):
    frame.pop()
    # null op while we don't support threads

@register_bytecode(195)
def monitorexit(vm, frame, offset, bytecode):
    frame.pop()
    # null op while we don't support threads
