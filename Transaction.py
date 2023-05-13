import base64
import hashlib
import json
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import time

from Script import Script


class Transaction:
    def __init__(self, data):
        if isinstance(data, Transaction):
            self.inputs = data.inputs
            self.outputs = data.outputs
            self.timestamp = data.timestamp if data.timestamp else time.time_ns()
        else:
            self.inputs = data['inputs']
            self.outputs = data['outputs']
            self.timestamp = data['timestamp'] if 'timestamp' in data.keys() else time.time_ns()
        self.h = hashlib.sha256(str(self).encode()).hexdigest()

    def __str__(self):
        return str((self.inputs, self.outputs, self.timestamp))

    def __repr__(self):
        return str((self.hash(), self.timestamp))

    def __eq__(self, other):
        other_tx = Transaction(other)
        res = True
        res = res and self.inputs == other_tx.inputs
        res = res and self.outputs == other_tx.outputs
        res = res and self.timestamp == other_tx.timestamp
        return res

    def hash(self):
        return self.h

    def as_dict(self):
        return self.__dict__.copy()

    def execute(self):
        for tx_input, tx_output in zip(self.inputs, self.outputs):
            unlocking_script = Script(tx_input["unlocking_script"])
            locking_script = Script(tx_output["locking_script"])
            stack = []

            if not unlocking_script.execute(stack) or not locking_script.execute(stack):
                return False

        return True

    @staticmethod
    def sign_transaction_input(private_key, transaction_hash, output_index):
        h = SHA256.new(f"{transaction_hash}:{output_index}".encode())
        signature = pkcs1_15.new(private_key).sign(h)
        return signature

    @staticmethod
    def verify_transaction_signature(public_key, transaction_hash, output_index, signature_str):
        # Convert the signature string back to bytes
        signature = base64.b64decode(signature_str.encode())

        h = SHA256.new(f"{transaction_hash}:{output_index}".encode())
        try:
            pkcs1_15.new(public_key).verify(h, signature)
            return True
        except (ValueError, TypeError):
            return False
