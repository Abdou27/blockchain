import base64
import hashlib
import json
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import time

from Script import Script


class Transaction:
    def __init__(self, data):
        """
        initializes the Transaction instance. If the provided data is of type Transaction, it sets the inputs, outputs,
        and timestamp to that of the given Transaction instance. Otherwise, it sets the inputs and outputs to the
        'inputs' and 'outputs' properties of the data dictionary, respectively, and sets the timestamp to the value of
        the 'timestamp' key in the data dictionary if it exists. Otherwise, it sets the timestamp to the current time in
        nanoseconds. It then calculates and sets the hash of the Transaction instance by applying the SHA256 hash
        function to the string representation of the instance.
        """
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
        """
        Returns a string representation of the Transaction instance consisting of the inputs, outputs, and timestamp.
        """
        return str((self.inputs, self.outputs, self.timestamp))

    def __repr__(self):
        """
        Returns a string representation of the Transaction instance consisting of the hash and timestamp.
        """
        return str((self.hash(), self.timestamp))

    def __eq__(self, other):
        """
        Returns True if the provided 'other' object is equal to the Transaction instance. Equality is defined as having
        the same inputs, outputs, and timestamp.
        """
        other_tx = Transaction(other)
        res = True
        res = res and self.inputs == other_tx.inputs
        res = res and self.outputs == other_tx.outputs
        res = res and self.timestamp == other_tx.timestamp
        return res

    def hash(self):
        """
        Returns the hash of the Transaction instance.
        """
        return self.h

    def as_dict(self):
        """
        Returns a copy of the Transaction instance's dictionary representation.
        """
        return self.__dict__.copy()

    def execute(self):
        """
        Executes the transaction by iterating over each input and output pair, applying their unlocking and locking
        scripts, respectively, and checking that the result is True for each pair. Returns True if all input/output
        pairs were successfully executed, False otherwise.
        """
        for tx_input, tx_output in zip(self.inputs, self.outputs):
            unlocking_script = Script(tx_input["unlocking_script"])
            locking_script = Script(tx_output["locking_script"])
            stack = []

            if not unlocking_script.execute(stack) or not locking_script.execute(stack):
                return False

        return True

    @staticmethod
    def sign_transaction_input(private_key, transaction_hash, output_index):
        """
        Creates a signature for the transaction input using the provided private key, transaction hash, and output
        index.
        """
        h = SHA256.new(f"{transaction_hash}:{output_index}".encode())
        signature = pkcs1_15.new(private_key).sign(h)
        return signature

    @staticmethod
    def verify_transaction_signature(public_key, transaction_hash, output_index, signature_str):
        """
        Verifies the signature of a transaction input by converting the provided signature string to bytes, hashing the
        string representation of the transaction hash and output index, and attempting to verify the signature using the
        provided public key and the hashed result. Returns True if the signature is valid, False otherwise.
        """
        # Convert the signature string back to bytes
        signature = base64.b64decode(signature_str.encode())

        h = SHA256.new(f"{transaction_hash}:{output_index}".encode())
        try:
            pkcs1_15.new(public_key).verify(h, signature)
            return True
        except (ValueError, TypeError):
            return False
