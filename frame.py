class Frame:
    operand_stack = None
    local_variables = None

    def __init__(self, this=None, parameters=[], max_stack=0, max_locals=0):
        self.stack = []
        self.local_variables = [None] * max_locals
        i=0
        if this:
            self.local_variables[i] = this
            i+=1
        for param in parameters:
            self.local_variables[i] = param
            i += 1
        self.max_stack=max_stack
        self.max_locals=max_locals

    def push(self, value):
        self.stack.append(value)
        assert len(self.stack) <= self.max_stack

    def pop(self):
        return self.stack.pop()

    def insert_local(self, index, value):
        self.local_variables[index] = value

    def get_local(self, index):
        return self.local_variables[index]
