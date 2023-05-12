import hashlib
import time


class Block:
    def __init__(self, transactions, previous_hash, **options):
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = options.get("nonce", 0)
        self.timestamp = options.get("timestamp", time.time_ns())

    def __repr__(self):
        return str((self.__get_transactions_as_dicts(), self.previous_hash, self.nonce, self.timestamp))

    def hash(self):
        return hashlib.sha256(repr(self).encode()).hexdigest()

    def as_dict(self):
        block_dict = self.__dict__.copy()
        block_dict["transactions"] = self.__get_transactions_as_dicts()
        return block_dict

    def __get_transactions_as_dicts(self):
        return list(map(lambda x: x.__dict__, self.transactions))
