import operator
import logging
import struct

from classconstants import void, null, ACC_STATIC
from klass import ClassInstance, ArrayClass

bytecodes = {}
def register_bytecode(start, end=-1, has_index=False):
    def decorator(f):
        if decorator.end == -1:
            decorator.end = decorator.start
        for i in xrange(decorator.start, decorator.end+1):
            assert i not in bytecodes
            bytecodes[i] = (decorator.start, f, has_index)
        return f
    decorator.start = start
    decorator.end = end
    return decorator

def decode_signed_offset(bytecode, pc):
    jump = struct.unpack('>h', chr(bytecode[pc+1])+chr(bytecode[pc+2]))[0]+pc-1
    logging.debug('offset %d' % jump)
    return jump

@register_bytecode(1)
def aconst_null(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(null)

@register_bytecode(2, 8)
def iconst_n(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(offset-1)

@register_bytecode(16)
def bipush(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(bytecode[pc+1])
    return pc+1

@register_bytecode(18)
def ldc(vm, klass, method, frame, offset, bytecode, pc):
    constant_pool_index = bytecode[pc+1]
    field = vm.resolve_field(klass, constant_pool_index)
    frame.push(field)
    return pc+1

@register_bytecode(19)
def ldc_w(vm, klass, method, frame, offset, bytecode, pc):
    constant_pool_index = (bytecode[pc+1] << 8) +  bytecode[pc+2]
    field = vm.resolve_field(klass, constant_pool_index)
    frame.push(field)
    return pc+2

@register_bytecode(21) #iload
@register_bytecode(22) #lload
@register_bytecode(25) #aload
def iload(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.get_local(bytecode[pc+1])
    if bytecode[pc] in (21, 22):
        assert isinstance(local, int)
    elif bytecode[pc] == 25:
        assert isinstance(local, (list, ClassInstance)) or local is null
    frame.push(local)
    return pc+1

@register_bytecode(26, 29)
@register_bytecode(30, 33)
def iload_n(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.get_local(offset)
    assert isinstance(local, int)
    frame.push(local)

@register_bytecode(34, 37)
def fload(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.get_local(offset)
    assert isinstance(local, float)
    frame.push(local)

@register_bytecode(42, 45)
def aload_n(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(frame.local_variables[offset])

@register_bytecode(46) #iaload
@register_bytecode(47) #laload
def iaload(vm, klass, method, frame, offset, bytecode, pc):
    index, array = frame.pop(), frame.pop()
    assert index >= 0
    frame.push(array[index])

@register_bytecode(51)
def baload(vm, klass, method, frame, offset, bytecode, pc):
    index, array = frame.pop(), frame.pop()
    print array
    raise Exception()

@register_bytecode(54) #istore
@register_bytecode(55) #lstore
@register_bytecode(58) #astore
def lstore(vm, klass, method, frame, offset, bytecode, pc):
    index = bytecode[pc+1]
    local = frame.pop()
    if bytecode[pc] in (54, 55):
        assert isinstance(local, int)
    elif bytecode[pc] == 58:
        assert isinstance(local, (list, ClassInstance)) or local is null
    frame.insert_local(index, local)
    return pc + 1


@register_bytecode(59, 62)
def istore_n(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.pop()
    assert isinstance(local, int)
    frame.insert_local(offset, local)

@register_bytecode(63, 66)
def lstore_n(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.pop()
    assert isinstance(local, int)
    frame.insert_local(offset, local)

@register_bytecode(75, 78)
def astore(vm, klass, method, frame, offset, bytecode, pc):
    reference = frame.pop()
    assert isinstance(reference, ClassInstance) or reference is null
    frame.insert_local(offset, reference)

@register_bytecode(79)
def iastore(vm, klass, method, frame, offset, bytecode, pc):
    value, index, array = frame.pop(), frame.pop(), frame.pop()
    assert array is not null
    assert index >= 0 and index < len(array)
    array[index] = value

@register_bytecode(87)
def pop(vm, klass, method, frame, offset, bytecode, pc):
    frame.pop()

@register_bytecode(88)
def pop2(vm, klass, method, frame, offset, bytecode, pc):
    frame.pop()
    frame.pop()


@register_bytecode(89)
def dup(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(frame.stack[-1])

@register_bytecode(96)
def iadd(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(int(frame.pop())+int(frame.pop()))

@register_bytecode(100)
def isub(vm, klass, method, frame, offset, bytecode, pc):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(b-a)

@register_bytecode(104) #imul
@register_bytecode(105) #lmul
def imul(vm, klass, method, frame, offset, bytecode, pc):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(a*b)

@register_bytecode(126)
def iand(vm, klass, method, frame, offset, bytecode, pc):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(a&b)

@register_bytecode(132)
def iinc(vm, klass, method, frame, offset, bytecode, pc):
    index, raw_const = bytecode[pc+1], bytecode[pc+2]
    start_value = frame.get_local(index)
    const = struct.unpack('>b', chr(raw_const))[0]
    frame.insert_local(index, start_value + const)
    assert isinstance(start_value, int)
    return pc + 2

def zero_comparison(name, operator):
    def comparison(vm, klass, method, frame, offset, bytecode, pc):
        a=frame.pop()
        assert isinstance(a, int)
        if operator(a, 0):
            return decode_signed_offset(bytecode, pc)
        return pc+2
    comparison.__name__ = name
    return comparison

ifeq = register_bytecode(153)(zero_comparison('ifeq', operator.eq))
ifne = register_bytecode(154)(zero_comparison('ifne', operator.ne))
iflt = register_bytecode(155)(zero_comparison('iflt', operator.lt))
ifge = register_bytecode(156)(zero_comparison('ifge', operator.ge))
ifgt = register_bytecode(157)(zero_comparison('ifgt', operator.gt))
ifle = register_bytecode(158)(zero_comparison('ifle', operator.le))

def integer_comparison(name, operator):
    def comparison(vm, klass, method, frame, offset, bytecode, pc):
        b, a = frame.pop(), frame.pop()
        assert isinstance(a, int) and isinstance(b, int)
        logging.debug('comparison %d %s %d' % (a, operator, b))
        if operator(a, b):
            return decode_signed_offset(bytecode, pc)
        return pc+2
    comparison.__name__ = name
    return comparison

if_cmpeq = register_bytecode(159)(integer_comparison('if_cmpeq', operator.eq))
if_cmpne = register_bytecode(160)(integer_comparison('if_cmpne', operator.ne))
if_cmplt = register_bytecode(161)(integer_comparison('if_cmplt', operator.lt))
if_cmpge = register_bytecode(162)(integer_comparison('if_cmpge', operator.ge))
if_cmpgt = register_bytecode(163)(integer_comparison('if_cmpgt', operator.gt))
if_cmple = register_bytecode(164)(integer_comparison('if_cmple', operator.le))

@register_bytecode(120) #ishl
@register_bytecode(121) #lshl
def ishl(vm, klass, method, frame, offset, bytecode, pc):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 63
    assert isinstance(value, int)
    frame.push(value << shift)

@register_bytecode(124) #iushr
@register_bytecode(125) #lushr
def iushr(vm, klass, method, frame, offset, bytecode, pc):
    shift, value = frame.pop(), frame.pop()
    assert 0 <= shift <= 63
    assert isinstance(value, int)
    frame.push(value >> shift)

@register_bytecode(128) #ior
@register_bytecode(129) #lor
def ior(vm, klass, method, frame, offset, bytecode, pc):
    val1, val2 = frame.pop(), frame.pop()
    assert isinstance(val1, int)
    assert isinstance(val2, int)
    frame.push(val1 | val2)

@register_bytecode(133) # i2l
@register_bytecode(136) # l2i
def i2l(vm, klass, method, frame, offset, bytecode, pc):
    return None

@register_bytecode(138)
def l2d(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(float(frame.pop()))

@register_bytecode(167)
def goto(vm, klass, method, frame, offset, bytecode, pc):
    return decode_signed_offset(bytecode, pc)

@register_bytecode(172)
def ireturn(vm, klass, method, frame, offset, bytecode, pc):
    return_value = int(frame.pop())
    assert not len(frame.stack)
    frame.return_value = return_value

@register_bytecode(176)
def areturn(vm, klass, method, frame, offset, bytecode, pc):
    return_value = frame.pop()
    assert isinstance(return_value, ClassInstance) or return_value is null
    assert not len(frame.stack)
    frame.return_value = return_value

@register_bytecode(177)
def return_(vm, klass, method, frame, offset, bytecode, pc):
    assert not frame.stack
    frame.return_value = void

@register_bytecode(178, has_index=True)
def getstatic(vm, klass, method, frame, offset, bytecode, pc):
    ref_index = vm.constant_pool_index(bytecode, pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass, ref_index)
    frame.push(field_klass.field_values[field_name])
    return pc + 2

@register_bytecode(179, has_index=True)
def putstatic(vm, klass, method, frame, offset, bytecode, pc):
    ref_index = vm.constant_pool_index(bytecode, pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass, ref_index)
    value = frame.pop()
    assert field_name in field_klass.fields
    field_klass.field_values[field_name] = value
    return pc + 2

@register_bytecode(180)
def getfield(vm, klass, method, frame, offset, bytecode, pc):
    field_index = vm.constant_pool_index(bytecode, pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass,
            field_index, 'Fieldref')
    objectref = frame.pop()
    assert isinstance(objectref, ClassInstance)
    frame.push( objectref.__getattr__(field_name))
    return pc + 2


@register_bytecode(181)
def putfield(vm, klass, method, frame, offset, bytecode, pc):
    field_index = vm.constant_pool_index(bytecode, pc)
    field_klass, field_name, field_descriptor = vm.resolve_field(klass,
            field_index, 'Fieldref')
    value, objectref = frame.pop(), frame.pop()
    assert isinstance(objectref, ClassInstance)
    objectref.__setattr__(field_name, value)
    return pc + 2

@register_bytecode(182)
@register_bytecode(183)
@register_bytecode(184)
def invokevirtual_special(vm, klass, method, frame, offset, bytecode, pc):
    method_index = vm.constant_pool_index(bytecode, pc)
    new_klass, method = vm.resolve_field(klass, method_index)
    logging.debug('GOT A CLASS %s.%s' % (new_klass, method))
    if bytecode[pc] == 184:
        assert (method.access_flags & ACC_STATIC) != 0
    vm.run_method(new_klass, method)
    return pc + 2

@register_bytecode(187)
def new(vm, klass, method, frame, offset, bytecode, pc):
    klass_index = vm.constant_pool_index(bytecode, pc)
    klass_name = klass.constant_pool.get_class(klass_index)
    logging.debug('creating class %s' % klass_name)
    klass = vm.load_class(klass_name)
    instance = ClassInstance(klass_name, klass)
    frame.push(instance)
    return pc  + 2

@register_bytecode(188)
def newarray(vm, klass, method, frame, offset, bytecode, pc):
    atype = bytecode[pc+1]
    #types = {4: 'str', 5: 'str', 6: 'float', 7: 'int', 8:

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    frame.push([0]*size)
    return pc + 1

@register_bytecode(189)
def anewarray(vm, klass, method, frame, offset, bytecode, pc):
    klass_name = klass.constant_pool.get_class(vm.constant_pool_index(bytecode, pc))
    klass = vm.load_class(klass_name)

    size = frame.pop()
    assert isinstance(size, int)
    assert size >= 0
    frame.push(ArrayClass(klass, size))
    return pc + 2

@register_bytecode(190)
def arraylength(vm, klass, method, frame, offset, bytecode, pc):
    arrayref = frame.pop()
    if isinstance(arrayref, list):
        frame.push(len(arrayref))
    elif isinstance(arrayref, ArrayClass):
        frame.push(arrayref.size)
    else:
        raise Exception

@register_bytecode(198)
def ifnull(vm, klass, method, frame, offset, bytecode, pc):
    return decode_signed_offset(bytecode, pc) if frame.pop() is null else pc+2

@register_bytecode(199)
def ifnonnull(vm, klass, method, frame, offset, bytecode, pc):
    return decode_signed_offset(bytecode, pc) if frame.pop() is not null else pc+2
