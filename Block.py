import hashlib
import time

from Transaction import Transaction


class Block:
    def __init__(self, transactions, previous_hash, **options):
        self.h = options.get("hash", None)
        self.previous_hash = previous_hash
        self.timestamp = options.get("timestamp", time.time_ns())
        self.nonce = options.get("nonce", 0)
        self.transactions = list(map(lambda x: Transaction(x), transactions))

    def __str__(self):
        return str((self.previous_hash, self._get_transactions_as_dicts(), self.nonce, self.timestamp))

    def __repr__(self):
        return str((self.h, self.previous_hash, self.nonce, self.timestamp))

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
        block_dict["transactions"] = self._get_transactions_as_dicts()
        return block_dict

    def _get_transactions_as_dicts(self):
        return list(map(lambda x: x.as_dict(), self.transactions))
