import hashlib


class Script:
    def __init__(self, code):
        """
        Initializes a new Script instance with the specified list of opcodes.
        """
        self.code = code

    def execute(self, stack):
        """
        Executes the script with the specified stack. Each opcode is processed one by one, modifying the stack as
        necessary. Returns True if the script executed successfully and False otherwise. The following opcodes are
        supported:
        - "OP_DUP": Duplicates the top element of the stack.
        - "OP_HASH160": Hashes the top element of the stack using SHA256. Pushes the resulting hash
        onto the stack.
        - "OP_EQUALVERIFY": Pops the top two elements of the stack and verifies if they are equal. If they are not
        equal, returns False.
        - Any other opcode: Pushes the opcode onto the stack.
        """
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
