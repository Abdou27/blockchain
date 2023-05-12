import hashlib


class Script:
    def __init__(self, code):
        self.code = code

    def execute(self, stack):
        for op in self.code:
            if op == "OP_DUP":
                stack.append(stack[-1])
            elif op == "OP_HASH160":
                stack.append(hashlib.sha256(stack.pop().encode()).hexdigest())
            elif op.startswith("OP_EQUALVERIFY"):
                if stack.pop() != stack.pop():
                    return False
            else:
                stack.append(op)
        return True
