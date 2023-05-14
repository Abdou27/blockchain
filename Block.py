import hashlib
import time

from MerkleTree import MerkleTree
from Transaction import Transaction


class Block:
    def __init__(self, i, transactions, previous_hash, **options):
        self.index = i
        self.h = options.get("hash", None)
        self.previous_hash = previous_hash
        self.timestamp = options.get("timestamp", time.time_ns())
        self.nonce = options.get("nonce", 0)
        self.merkle_tree = MerkleTree(transactions)

    def __str__(self):
        return str((self.index, self.previous_hash, self.merkle_tree.get_root().hash, self.nonce, self.timestamp))

    def __repr__(self):
        return str((self.index, self.h, self.previous_hash, self.nonce, self.timestamp))

    def __eq__(self, other):
        res = True
        res = res and self.previous_hash == other.previous_hash
        res = res and self.hash() == other.hash()
        res = res and self.timestamp == other.timestamp
        res = res and self.nonce == other.nonce
        # Not necessary to check the transactions
        return res

    def hash(self):
        self.h = hashlib.sha256(str(self).encode()).hexdigest()
        return self.h

    def as_dict(self):
        block_dict = self.__dict__.copy()
        block_dict["merkle_tree"] = self.merkle_tree.as_dict()
        return block_dict

    def transactions(self):
        return self.merkle_tree.transactions
