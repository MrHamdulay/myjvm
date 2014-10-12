from vm import register_bytecode, void, null

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
    frame.push(frame.get_local(offset))

@register_bytecode(42, 45)
def aload_n(vm, klass, method, frame, offset, bytecode, pc):
    frame.push(frame.local_variables[offset])

@register_bytecode(59, 62)
def istore_n(vm, klass, method, frame, offset, bytecode, pc):
    frame.insert_local(offset, frame.pop())

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
    return self.constant_pool_index(bytecode, pc)

@register_bytecode(172)
def ireturn(vm, klass, method, frame, offset, bytecode, pc):
    return_value = int(frame.pop())
    assert not frame.stack
    return return_value

@register_bytecode(177)
def ireturn(vm, klass, method, frame, offset, bytecode, pc):
    frame.return_value = void
