import operator
import logging
import struct

bytecodes = {}

from rpython.rlib.rarithmetic import intmask, longlongmask

from classconstants import void, null, ACC_STATIC
from klass import Class, ClassInstance, ArrayClass

def register_bytecode(start, end=-1, use_next=0):
    def decorator(f):
        if decorator.end == -1:
            decorator.end = decorator.start
        for i in xrange(decorator.start, decorator.end+1):
            assert i not in bytecodes
            bytecodes[i] = (decorator.start, f, use_next)
        return f
    decorator.start = start
    decorator.end = end
    return decorator

def decode_signed_offset(bytecode, pc):
    jump = struct.unpack('>h', chr(bytecode[pc+1])+chr(bytecode[pc+2]))[0]+pc-1
    return jump

@register_bytecode(1)
def aconst_null(vm, klass, method, frame, offset, bytecode):
    frame.push(null)

@register_bytecode(2, 8)
def iconst_n(vm, klass, method, frame, offset, bytecode):
    frame.push(offset-1)

@register_bytecode(16, use_next=1)
def bipush(vm, klass, method, frame, offset, bytecode):
    frame.push(bytecode[frame.pc+1])
    frame.pc = frame.pc+1

@register_bytecode(18, use_next=1)
def ldc(vm, klass, method, frame, offset, bytecode):
    constant_pool_index = bytecode[frame.pc+1]
    field = vm.resolve_field(klass, constant_pool_index)
    frame.push(field)
    frame.pc = frame.pc+1

@register_bytecode(19, use_next=2)
def ldc_w(vm, klass, method, frame, offset, bytecode):
    constant_pool_index = (bytecode[frame.pc+1] << 8) +  bytecode[frame.pc+2]
    field = vm.resolve_field(klass, constant_pool_index)
    frame.push(field)
    frame.pc = frame.pc+2

@register_bytecode(21, use_next=1) #iload
@register_bytecode(22, use_next=1) #lload
@register_bytecode(25, use_next=1) #aload
def iload(vm, klass, method, frame, offset, bytecode):
    local = frame.get_local(bytecode[frame.pc+1])
    if bytecode[frame.pc] in (21, 22):
        assert isinstance(local, (long, int))
    elif bytecode[frame.pc] == 25:
        assert isinstance(local, (list, ClassInstance)) or local is null
    frame.push(local)
    frame.pc = frame.pc+1

@register_bytecode(26, 29)
@register_bytecode(30, 33)
def iload_n(vm, klass, method, frame, offset, bytecode):
    local = frame.get_local(offset)
    assert isinstance(local, int)
    frame.push(local)

@register_bytecode(34, 37)
def fload(vm, klass, method, frame, offset, bytecode):
    local = frame.get_local(offset)
    assert isinstance(local, float)
    frame.push(local)

@register_bytecode(42, 45)
def aload_n(vm, klass, method, frame, offset, bytecode):
    val = frame.local_variables[offset]
    assert isinstance(val, (Class, ClassInstance)) or val is null
    frame.push(val)

@register_bytecode(46) #iaload
@register_bytecode(47) #laload
def iaload(vm, klass, method, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    assert index >= 0
    frame.push(array[index])

@register_bytecode(51)
def baload(vm, klass, method, frame, offset, bytecode):
    index, array = frame.pop(), frame.pop()
    raise Exception()

@register_bytecode(54, use_next=1) #istore
@register_bytecode(55, use_next=1) #lstore
@register_bytecode(58, use_next=1) #astore
def lstore(vm, klass, method, frame, offset, bytecode):
    index = bytecode[frame.pc+1]
    local = frame.pop()
    if bytecode[frame.pc] in (54, 55):
        assert isinstance(local, (int, long))
    elif bytecode[frame.pc] == 58:
        assert isinstance(local, (list, ClassInstance)) or local is null
    frame.insert_local(index, local)
    frame.pc = frame.pc + 1


@register_bytecode(59, 62)
def istore_n(vm, klass, method, frame, offset, bytecode):
    local = frame.pop()
    assert isinstance(local, int)
    frame.insert_local(offset, local)

@register_bytecode(63, 66)
def lstore_n(vm, klass, method, frame, offset, bytecode):
    local = frame.pop()
    assert isinstance(local, int)
    frame.insert_local(offset, local)

@register_bytecode(75, 78)
def astore(vm, klass, method, frame, offset, bytecode):
    reference = frame.pop()
    assert isinstance(reference, ClassInstance) or reference is null
    frame.insert_local(offset, reference)

@register_bytecode(79)
def iastore(vm, klass, method, frame, offset, bytecode):
    value, index, array = intmask(frame.pop()), frame.pop(), frame.pop()
    assert array is not null
    assert index >= 0 and index < len(array)
    array[index] = value

@register_bytecode(87)
def pop(vm, klass, method, frame, offset, bytecode):
    frame.pop()

@register_bytecode(88)
def pop2(vm, klass, method, frame, offset, bytecode):
    frame.pop()
    frame.pop()


@register_bytecode(89)
def dup(vm, klass, method, frame, offset, bytecode):
    frame.push(frame.stack[-1])

@register_bytecode(96)
def iadd(vm, klass, method, frame, offset, bytecode):
    frame.push(intmask(frame.pop()+frame.pop()))

@register_bytecode(100)
def isub(vm, klass, method, frame, offset, bytecode):
    a, b = intmask(frame.pop()), intmask(frame.pop())
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(b-a))

@register_bytecode(104)
def imul(vm, klass, method, frame, offset, bytecode):
    a, b = intmask(frame.pop()), intmask(frame.pop())
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(a*b))

@register_bytecode(105)
def lmul(vm, klass, method, frame, offset, bytecode):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, (int, long)) and isinstance(b, (int, long))
    frame.push(longlongmask(a*b))

@register_bytecode(126)
def iand(vm, klass, method, frame, offset, bytecode):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(intmask(a&b))

@register_bytecode(132, use_next=2)
def iinc(vm, klass, method, frame, offset, bytecode):
    index, raw_const = bytecode[frame.pc+1], bytecode[frame.pc+2]
    start_value = frame.get_local(index)
    const = struct.unpack('>b', chr(raw_const))[0]
    frame.insert_local(index, intmask(start_value + const))
    assert isinstance(start_value, int)
    frame.pc = frame.pc + 2

def zero_comparison(name, operator):
    def comparison(vm, klass, method, frame, offset, bytecode):
        a=frame.pop()
        assert isinstance(a, int)
        if operator(a, 0):
            frame.pc = decode_signed_offset(bytecode, frame.pc)
            return
        frame.pc = frame.pc+2
    comparison.__name__ = name
    return comparison

ifeq = register_bytecode(153)(zero_comparison('ifeq', operator.eq))
ifne = register_bytecode(154)(zero_comparison('ifne', operator.ne))
iflt = register_bytecode(155)(zero_comparison('iflt', operator.lt))
ifge = register_bytecode(156)(zero_comparison('ifge', operator.ge))
ifgt = register_bytecode(157)(zero_comparison('ifgt', operator.gt))
ifle = register_bytecode(158)(zero_comparison('ifle', operator.le))

def integer_comparison(name, operator):
    def comparison(vm, klass, method, frame, offset, bytecode):
        b, a = frame.pop(), frame.pop()
        assert isinstance(a, int) and isinstance(b, int)
        if operator(a, b):
            frame.pc = decode_signed_offset(bytecode, frame.pc)
            return
        frame.pc = frame.pc+2
    comparison.__name__ = name
    return comparison

if_cmpeq = register_bytecode(159)(integer_comparison('if_cmpeq', operator.eq))
if_cmpne = register_bytecode(160)(integer_comparison('if_cmpne', operator.ne))
if_cmplt = register_bytecode(161)(integer_comparison('if_cmplt', operator.lt))
if_cmpge = register_bytecode(162)(integer_comparison('if_cmpge', operator.ge))
if_cmpgt = register_bytecode(163)(integer_comparison('if_cmpgt', operator.gt))
if_cmple = register_bytecode(164)(integer_comparison('if_cmple', operator.le))

@register_bytecode(120) #ishl
def ishl(vm, klass, method, frame, offset, bytecode):
    shift, value = frame.pop(), intmask(frame.pop())
    assert 0 <= shift <= 31
    frame.push(intmask(value << shift))

@register_bytecode(121) #lshl
def lshl(vm, klass, method, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 63
    frame.push(longlongmask(value << shift))

@register_bytecode(124) #iushr
def iushr(vm, klass, method, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 31
    assert isinstance(value, int)
    frame.push(intmask(value >> shift))

@register_bytecode(125) #lushr
def lushr(vm, klass, method, frame, offset, bytecode):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 63
    frame.push(longlongmask(value >> shift))

@register_bytecode(128) #ior
def ior(vm, klass, method, frame, offset, bytecode):
    val1, val2 = intmask(frame.pop()), intmask(frame.pop())
    frame.push(intmask(val1 | val2))

@register_bytecode(129) #lor
def lor(vm, klass, method, frame, offset, bytecode):
    val1, val2 = frame.pop(), frame.pop()
    frame.push(longlongmask(val1 | val2))

@register_bytecode(130)
def ixor(vm, klass, method, frame, offset, bytecode):
    val1, val2 = frame.pop(), frame.pop()
    frame.push(intmask(val1 ^ val2))

@register_bytecode(131)
def lxor(vm, klass, method, frame, offset, bytecode):
    val1, val2 = frame.pop(), frame.pop()
    frame.push(longlongmask(val1 ^ val2))

@register_bytecode(133) # i2l
@register_bytecode(136) # l2i
def i2l(vm, klass, method, frame, offset, bytecode):
    return None

@register_bytecode(138)
def l2d(vm, klass, method, frame, offset, bytecode):
    frame.push(float(frame.pop()))

@register_bytecode(167)
def goto(vm, klass, method, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc)

@register_bytecode(172)
def ireturn(vm, klass, method, frame, offset, bytecode):
    return_value = int(frame.pop())
    assert not len(frame.stack)
    frame.return_value = return_value

@register_bytecode(176)
def areturn(vm, klass, method, frame, offset, bytecode):
    return_value = frame.pop()
    assert isinstance(return_value, ClassInstance) or return_value is null
    assert not len(frame.stack)
    frame.return_value = return_value

@register_bytecode(177)
def return_(vm, klass, method, frame, offset, bytecode):
    assert not frame.stack
    frame.return_value = void

@register_bytecode(178, use_next=2)
def getstatic(vm, klass, method, frame, offset, bytecode):
    ref_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass, ref_index)
    frame.push(field_klass.field_values[field_name])
    frame.pc = frame.pc + 2

@register_bytecode(179, use_next=2)
def putstatic(vm, klass, method, frame, offset, bytecode):
    ref_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass, ref_index)
    value = frame.pop()
    assert field_name in field_klass.fields
    field_klass.field_values[field_name] = value
    frame.pc = frame.pc + 2

@register_bytecode(180, use_next=2)
def getfield(vm, klass, method, frame, offset, bytecode):
    field_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass,
            field_index, 'Fieldref')
    objectref = frame.pop()
    if objectref is null:
        vm.throw_exception(frame, 'java/lang/NullPointerException')
    else:
        assert isinstance(objectref, ClassInstance)
        frame.push( objectref.__getattr__(field_name))
    frame.pc = frame.pc + 2


@register_bytecode(181, use_next=2)
def putfield(vm, klass, method, frame, offset, bytecode):
    field_index = vm.constant_pool_index(bytecode, frame.pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass,
            field_index, 'Fieldref')
    value, objectref = frame.pop(), frame.pop()
    assert isinstance(objectref, ClassInstance) or objectref is null
    objectref.__setattr__(field_name, value)
    frame.pc = frame.pc + 2

@register_bytecode(182, use_next=2)
@register_bytecode(183, use_next=2)
@register_bytecode(184, use_next=2)
def invokevirtual_special(vm, klass, method, frame, offset, bytecode):
    method_index = vm.constant_pool_index(bytecode, frame.pc)
    new_klass, method = vm.resolve_field(klass, method_index)
    if bytecode[frame.pc] == 184:
        assert (method.access_flags & ACC_STATIC) != 0
    vm.run_method(new_klass, method)
    frame.pc = frame.pc + 2

@register_bytecode(187, use_next=2)
def new(vm, klass, method, frame, offset, bytecode):
    klass_index = vm.constant_pool_index(bytecode, frame.pc)
    klass_name = klass.constant_pool.get_class(klass_index)
    klass = vm.load_class(klass_name)
    instance = klass.instantiate()
    frame.push(instance)
    frame.pc = frame.pc  + 2

@register_bytecode(188, use_next=1)
def newarray(vm, klass, method, frame, offset, bytecode):
    atype = bytecode[frame.pc+1]
    #types = {4: 'str', 5: 'str', 6: 'float', 7: 'int', 8:

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    frame.push([0]*size)
    frame.pc = frame.pc + 1

@register_bytecode(189, use_next=2)
def anewarray(vm, klass, method, frame, offset, bytecode):
    klass_name = klass.constant_pool.get_class(vm.constant_pool_index(bytecode, frame.pc))
    klass = vm.load_class(klass_name)

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    frame.push(ArrayClass(klass, size))
    frame.pc = frame.pc + 2

@register_bytecode(190)
def arraylength(vm, klass, method, frame, offset, bytecode):
    arrayref = frame.pop()
    if isinstance(arrayref, list):
        frame.push(len(arrayref))
    elif isinstance(arrayref, ArrayClass):
        frame.push(arrayref.size)
    else:
        raise Exception

@register_bytecode(191)
def athrow(vm, klass, method, frame, offset, bytecode):
    frame.raised_exception = frame.pop()

@register_bytecode(193, use_next=2)
def instanceof(vm, klass, method, frame, offset, bytecode):
    objectref = frame.pop()
    if objectref is null:
        frame.push(0)
        frame.pc = frame.pc+2
        return
    klass = vm.load_class(klass.constant_pool.get_class(vm.constant_pool_index(bytecode, frame.pc)))
    frame.push(1 if klass.is_subclass(objectref) else 0)
    frame.pc = frame.pc+2


@register_bytecode(198)
def ifnull(vm, klass, method, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc) if frame.pop() is null else frame.pc+2

@register_bytecode(199, use_next=2)
def ifnonnull(vm, klass, method, frame, offset, bytecode):
    frame.pc = decode_signed_offset(bytecode, frame.pc) if frame.pop() is not null else frame.pc+2

@register_bytecode(194)
def monitorenter(vm, klass, method, frame, offset, bytecode):
    frame.pop()
    # null op while we don't support threads

@register_bytecode(195)
def monitorexit(vm, klass, method, frame, offset, bytecode):
    frame.pop()
    # null op while we don't support threads
