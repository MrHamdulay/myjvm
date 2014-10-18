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
    jump = struct.unpack('>h', chr(bytecode[pc+1])+chr(bytecode[pc+2]))[0]+pc
    logging.debug('offset %d' % jump)
    return jump

@register_bytecode(1)
def aconst_null(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(null)

@register_bytecode(2, 8)
def iconst_n(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(offset)

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

@register_bytecode(22)
def iload(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.get_local(bytecode[pc+1])
    assert isinstance(local, int)
    frame.push(local)
    return pc+1

@register_bytecode(26, 29)
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

@register_bytecode(55)
def lstore(vm, klass, method, frame, offset, bytecode, pc):
    index = bytecode[pc+1]
    local = frame.pop()
    assert isinstance(local, int)
    frame.insert_local(index, local)
    return pc + 1

@register_bytecode(59, 62)
def istore_n(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.pop()
    assert isinstance(local, int)
    frame.insert_local(offset, local)

@register_bytecode(75, 78)
def astore(vm, klass, method, frame, offset, bytecode, pc):
    reference = frame.pop()
    assert isinstance(reference, ClassInstance)
    frame.insert_local(offset, reference)

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
    frame.push(a-b)

@register_bytecode(126)
def iand(vm, klass, method, frame, offset, bytecode, pc):
    a, b = frame.pop(), frame.pop()
    assert isinstance(a, int) and isinstance(b, int)
    frame.push(a&b)

def zero_comparison(name, operator):
    def comparison(vm, klass, method, frame, offset, bytecode, pc):
        a=frame.pop()
        assert isinstance(a, int)
        if operator(a, 0):
            return decode_signed_offset(bytecode, pc)
        return pc+1
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
        a, b = frame.pop(), frame.pop()
        assert isinstance(a, int) and isinstance(b, int)
        if operator(a, b):
            return decode_signed_offset(bytecode, pc)
        return pc+1
    comparison.__name__ = name
    return comparison

if_cmpeq = register_bytecode(159)(integer_comparison('if_cmpeq', operator.eq))
if_cmpne = register_bytecode(160)(integer_comparison('if_cmpne', operator.ne))
if_cmplt = register_bytecode(161)(integer_comparison('if_cmplt', operator.lt))
if_cmpge = register_bytecode(162)(integer_comparison('if_cmpge', operator.ge))
if_cmpgt = register_bytecode(163)(integer_comparison('if_cmpgt', operator.gt))
if_cmple = register_bytecode(164)(integer_comparison('if_cmple', operator.le))

@register_bytecode(133)
def i2l(vm, klass, method, frame, offset, bytecode, pc):
    return None

@register_bytecode(138)
def l2d(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(float(frame.pop()))

@register_bytecode(167)
def goto(vm, klass, method, frame, offset, bytecode, pc):
    return vm.constant_pool_index(bytecode, pc)

@register_bytecode(172)
def ireturn(vm, klass, method, frame, offset, bytecode, pc):
    return_value = int(frame.pop())
    assert not frame.stack
    frame.return_value = return_value

@register_bytecode(177)
def return_(vm, klass, method, frame, offset, bytecode, pc):
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
    klass, method = vm.resolve_field(klass, method_index)
    if bytecode[pc] == 184:
        assert (method.access_flags & ACC_STATIC) != 0
    vm.run_method(klass, method)
    return pc + 2

@register_bytecode(187)
def new(vm, klass, method, frame, offset, bytecode, pc):
    klass_index = vm.constant_pool_index(bytecode, pc)
    klass_name = klass.constant_pool.get_class(klass_index)
    klass = vm.load_class(klass_name)
    instance = ClassInstance(klass_name, klass)
    frame.push(instance)
    return pc  + 2

@register_bytecode(189)
def anewarray(vm, klass, method, frame, offset, bytecode, pc):
    klass_name = klass.constant_pool.get_class(vm.constant_pool_index(bytecode, pc))
    klass = vm.load_class(klass_name)

    size = frame.pop()
    assert isinstance(size, int)
    frame.push(ArrayClass(klass, size))
    return pc + 2
