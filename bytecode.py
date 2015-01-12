import operator
import logging
import struct
import math

bytecodes = {}

from rpython.rlib.rarithmetic import intmask, longlongmask

from classconstants import *
from klass import Class, ClassInstance, ArrayClass
from descriptor import parse_descriptor, descriptor_is_array

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
    jump = struct.unpack('>h', chr(bytecode[pc+1])+chr(bytecode[pc+2]))[0]+pc-1
    return jump

@register_bytecode(1)
def aconst_null(vm, frame, offset, bytecode):
    frame.push(null)

@register_bytecode(2, 8)
def iconst_n(vm, frame, offset, bytecode):
    frame.push(offset-1)

@register_bytecode(11, 13)
def fconst_n(vm, frame, offset, bytecode):
    frame.push(float(offset))

@register_bytecode(16, use_next=1)
def bipush(vm, frame, offset, bytecode):
    frame.push(bytecode[frame.pc+1])
    frame.pc = frame.pc+1

@register_bytecode(17, use_next=2)
def sipush(vm, frame, offset, bytecode):
    frame.push((bytecode[frame.pc+1]<<8) | bytecode[frame.pc+2])
    frame.pc = frame.pc+2

@register_bytecode(18, use_next=1)
def ldc(vm, frame, offset, bytecode):
    constant_pool_index = bytecode[frame.pc+1]
    field = vm.resolve_field(frame.klass, constant_pool_index)
    frame.push(field)
    frame.pc = frame.pc+1

@register_bytecode(19, use_next=2)
def ldc_w(vm, frame, offset, bytecode):
    constant_pool_index = (bytecode[frame.pc+1] << 8) +  bytecode[frame.pc+2]
    field = vm.resolve_field(frame.klass, constant_pool_index)
    frame.push(field)
    frame.pc = frame.pc+2

@register_bytecode(20, use_next=2)
def ldc2_w(vm, frame, offset, bytecode):
    index = (bytecode[frame.pc+1] << 8) +  bytecode[frame.pc+2]
    field = klass.constant_pool.get_object((CONSTANT_Double, CONSTANT_Long), index)[0][0]
    assert isinstance(field, (float, int, long)), 'incorrect type %s' % str(field)
    frame.push(field)
    frame.pc = frame.pc+2

@register_bytecode(21, use_next=1) #iload
@register_bytecode(22, use_next=1) #lload
@register_bytecode(25, use_next=1) #aload
def iload(vm, frame, offset, bytecode):
    local = frame.get_local(bytecode[frame.pc+1])
    if bytecode[frame.pc] in (21, 22):
        assert isinstance(local, (long, int))
    elif bytecode[frame.pc] == 25:
        assert isinstance(local, (list, ClassInstance)) or local is null
    frame.push(local)
    frame.pc = frame.pc+1

def iload_n_repr(vm, frame, index, offset, bytecode):
    return str(offset)

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
    assert isinstance(val, (Class, ClassInstance, ArrayClass)) or val is null
    frame.push(val)

@register_bytecode(46) #iaload
@register_bytecode(47) #laload
def iaload(vm, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    assert index >= 0
    frame.push(array[index])

@register_bytecode(51)
def baload(vm, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    raise Exception()

@register_bytecode(54, use_next=1) #istore
@register_bytecode(55, use_next=1) #lstore
@register_bytecode(58, use_next=1) #astore
def lstore(vm, frame, offset, bytecode):
    index = bytecode[frame.pc+1]
    local = frame.pop()
    if bytecode[frame.pc] in (54, 55):
        assert isinstance(local, (int, long))
    elif bytecode[frame.pc] == 58:
        assert isinstance(local, (list, ClassInstance)) or local is null
    frame.insert_local(index, local)
    frame.pc = frame.pc + 1

def istore_n_repr(vm, frame, index, offset, bytecode):
    return str(offset)

@register_bytecode(59, 62, bc_repr=istore_n_repr)
def istore_n(vm, frame, offset, bytecode):
    local = frame.pop()
    frame.insert_local(offset, intmask(local))

@register_bytecode(63, 66, bc_repr=istore_n_repr)
def lstore_n(vm, frame, offset, bytecode):
    local = frame.pop()
    frame.insert_local(offset, longlongmask(local))

@register_bytecode(75, 78)
def astore(vm, frame, offset, bytecode):
    reference = frame.pop()
    print reference
    assert isinstance(reference, (ArrayClass, ClassInstance)) or reference is null
    frame.insert_local(offset, reference)

@register_bytecode(79)
def iastore(vm, frame, offset, bytecode):
    value, index, array = intmask(frame.pop()), frame.pop(), frame.pop()
    assert array is not null
    assert index >= 0 and index < len(array)
    array[index] = value

@register_bytecode(83)
def aastore(vm, frame, offset, bytecode):
    value, index, arrayref = frame.pop(), frame.pop(), frame.pop()
    print arrayref, index, value

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

@register_bytecode(96)
def iadd(vm, frame, offset, bytecode):
    frame.push(intmask(frame.pop()+frame.pop()))

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
            frame.pc = decode_signed_offset(bytecode, frame.pc)
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
            frame.pc = decode_signed_offset(bytecode, frame.pc)
            return
        frame.pc = frame.pc+2
    comparison.__name__ = name
    return comparison

if_cmpeq = register_bytecode(159, use_next=2)(
        integer_comparison('if_cmpeq', operator.eq))
if_cmpne = register_bytecode(160, use_next=2)(
        integer_comparison('if_cmpne', operator.ne))
if_cmplt = register_bytecode(161, use_next=2)(
        integer_comparison('if_cmplt', operator.lt))
if_cmpge = register_bytecode(162, use_next=2)(
        integer_comparison('if_cmpge', operator.ge))
if_cmpgt = register_bytecode(163, use_next=2)(
        integer_comparison('if_cmpgt', operator.gt))
if_cmple = register_bytecode(164, use_next=2)(
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
    frame.push(longlongmask(value << shift))

@register_bytecode(124) #iushr
def iushr(vm, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 31
    assert isinstance(value, int)
    frame.push(intmask(value >> shift))

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
    return None

@register_bytecode(138)
def l2d(vm, frame, offset, bytecode):
    frame.push(float(frame.pop()))

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

@register_bytecode(167, use_next=2)
def goto(vm, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc)

@register_bytecode(172)
def ireturn(vm, frame, offset, bytecode):
    return_value = int(frame.pop())
    assert not len(frame.stack)
    frame.return_value = intmask(return_value)

@register_bytecode(173)
def lreturn(vm, frame, offset, bytecode):
    return_value = frame.pop()
    assert not len(frame.stack)
    frame.return_value = longlongmask(return_value)

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
    return ' '.join(map(str, vm.resolve_field(frame.klass, ref_index)))

@register_bytecode(178, use_next=2, bc_repr=getstatic_repr)
def getstatic(vm, frame, offset, bytecode):
    ref_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(
            frame.klass, ref_index)
    frame.push(field_klass.field_values[field_name])
    frame.pc = frame.pc + 2

@register_bytecode(179, use_next=2, bc_repr=getstatic_repr)
def putstatic(vm, frame, offset, bytecode):
    ref_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(frame.klass, ref_index)
    value = frame.pop()
    assert field_name in field_klass.fields
    field_klass.field_values[field_name] = value
    frame.pc = frame.pc + 2

@register_bytecode(180, use_next=2)
def getfield(vm, frame, offset, bytecode):
    field_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(
            frame.klass, field_index, 'Fieldref')
    objectref = frame.pop()
    if objectref is null:
        vm.throw_exception(frame, 'java/lang/NullPointerException')
    else:
        assert isinstance(objectref, ClassInstance)
        frame.push( objectref.__getattr__(field_name))
    frame.pc = frame.pc + 2


@register_bytecode(181, use_next=2)
def putfield(vm, frame, offset, bytecode):
    field_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(
            frame.klass, field_index, 'Fieldref')
    value, objectref = frame.pop(), frame.pop()
    assert isinstance(objectref, ClassInstance) or objectref is null
    objectref.__setattr__(field_name, value)
    frame.pc = frame.pc + 2

def invokevirtual_repr(vm, frame, index, offset, bytecode):
    ref_index = (bytecode[index+1]<<8) | (bytecode[index+2])
    new_klass, method = vm.resolve_field(frame.klass, ref_index)
    return '%s.%s %s' % (new_klass.name, method.name, method.descriptor)

@register_bytecode(182, use_next=2, bc_repr=invokevirtual_repr)
@register_bytecode(183, use_next=2, bc_repr=invokevirtual_repr)
@register_bytecode(184, use_next=2, bc_repr=invokevirtual_repr)
def invokevirtual_special(vm, frame, offset, bytecode):
    method_index = vm.constant_pool_index(bytecode, frame.pc)
    new_klass, method = vm.resolve_field(frame.klass, method_index)
    if bytecode[frame.pc] == 184:
        assert (method.access_flags & ACC_STATIC) != 0
    vm.run_method(new_klass, method)
    frame.pc = frame.pc + 2

@register_bytecode(185, use_next=4)
def invokeinterface(vm, frame, offset, bytecode):
    raise Exception()

@register_bytecode(187, use_next=2)
def new(vm, frame, offset, bytecode):
    klass_index = vm.constant_pool_index(bytecode, frame.pc)
    klass_name = frame.klass.constant_pool.get_class(klass_index)
    klass = vm.load_class(klass_name)
    instance = klass.instantiate()
    frame.push(instance)
    frame.pc = frame.pc  + 2

@register_bytecode(188, use_next=1)
def newarray(vm, frame, offset, bytecode):
    atype = bytecode[frame.pc+1]
    #types = {4: 'str', 5: 'str', 6: 'float', 7: 'int', 8:

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    frame.push([0]*size)
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
    if isinstance(arrayref, list):
        frame.push(len(arrayref))
    elif isinstance(arrayref, ArrayClass):
        frame.push(arrayref.size)
    else:
        raise Exception

@register_bytecode(191)
def athrow(vm, frame, offset, bytecode):
    frame.raised_exception = frame.pop()

def _checkcast(vm, frame, reference, descriptor):
    print reference, descriptor
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
    print(reference)
    descriptor = frame.klass.constant_pool.get_class(
        vm.constant_pool_index(bytecode, frame.pc-2))
    print descriptor
    if descriptor[0] == '[':
        descriptor = parse_descriptor(descriptor)[0]

    if _checkcast(vm, frame, reference, descriptor):
        frame.push(reference)
    else:
        frame.raised_exception = 'ClassCastException'


@register_bytecode(193, use_next=2)
def instanceof(vm, frame, offset, bytecode):
    objectref = frame.pop()
    frame.pc += 2
    if objectref is null:
        frame.push(0)
        return
    klass = vm.load_class(klass.constant_pool.get_class(vm.constant_pool_index(bytecode, frame.pc)))
    frame.push(1 if klass.is_subclass(objectref) else 0)


@register_bytecode(198, use_next=2)
def ifnull(vm, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc) if frame.pop() is null else frame.pc+2

@register_bytecode(199, use_next=2)
def ifnonnull(vm, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc) if frame.pop() is not null else frame.pc+2

@register_bytecode(194)
def monitorenter(vm, frame, offset, bytecode):
    frame.pop()
    # null op while we don't support threads

@register_bytecode(195)
def monitorexit(vm, frame, offset, bytecode):
    frame.pop()
    # null op while we don't support threads
