import hashlib
import random
import time


class Block:
    def __init__(self, transactions, previous_hash):
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.timestamp = time.time()

    def __repr__(self):
        return str((self.transactions, self.previous_hash, self.nonce))

    def hash(self):
        return hashlib.sha256(repr((self.transactions, self.previous_hash, self.nonce)).encode()).hexdigest()