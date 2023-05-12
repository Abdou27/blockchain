import json
import time

from Script import Script


class Transaction:
    def __init__(self, inputs, outputs, timestamp=None):
        self.inputs = inputs
        self.outputs = outputs
        self.timestamp = timestamp if timestamp else time.time_ns()

    def __repr__(self):
        return str((self.inputs, self.outputs, self.timestamp))

    def __eq__(self, other):
        res = True
        res = res and self.inputs == other.inputs
        res = res and self.outputs == other.outputs
        res = res and self.timestamp == other.timestamp
        return res

    def execute(self):
        for tx_input, tx_output in zip(self.inputs, self.outputs):
            unlocking_script = Script(tx_input["unlocking_script"])
            locking_script = Script(tx_output["locking_script"])
            stack = []

            if not unlocking_script.execute(stack) or not locking_script.execute(stack):
                return False

        return True
