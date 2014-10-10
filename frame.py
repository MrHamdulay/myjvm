class Frame:
    operand_stack = None
    local_variables = None

    def __init__(self, this=None, parameters=[], max_stack=0, max_locals=0):
        self.stack = []
        self.local_variables = [this] + parameters
        self.max_stack=max_stack
        self.max_locals=max_locals

