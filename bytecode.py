from classconstants import void, null, ACC_STATIC
from klass import ClassInstance

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

@register_bytecode(26, 29)
def iload_n(vm, klass, method, frame, offset, bytecode, pc):
    local = frame.get_local(offset)
    assert isinstance(local, int)
    frame.push(local)

@register_bytecode(42, 45)
def aload_n(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(frame.local_variables[offset])

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
