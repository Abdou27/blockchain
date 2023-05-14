import hashlib
import time

from MerkleTree import MerkleTree


class Block:
    def __init__(self, i, transactions, previous_hash, **options):
        """
        Constructor for Block class.

        Parameters:
            i (int): Index of the block in the chain.
            transactions (list): List of Transaction objects.
            previous_hash (str): Hash of the previous block in the chain.
            **options (dict): Optional parameters for the block.
        """
        self.index = i
        self.h = options.get("hash", None)  # optional hash parameter, defaults to None
        self.previous_hash = previous_hash
        self.timestamp = options.get("timestamp",
                                     time.time_ns())  # optional timestamp parameter, defaults to current time
        self.nonce = options.get("nonce", 0)  # optional nonce parameter, defaults to 0
        self.merkle_tree = MerkleTree(transactions)

    def __str__(self):
        """
        Returns a string representation of the block, used in hashing.
        """
        return str((self.index, self.previous_hash, self.merkle_tree.get_root().hash, self.nonce, self.timestamp))

    def __repr__(self):
        """
        Returns a string representation of the block, used for debugging.
        """
        return str((self.index, self.h, self.previous_hash, self.nonce, self.timestamp))

    def __eq__(self, other):
        """
        Compares two blocks and returns True if they are equal.

        Parameters:
            other (Block): Block object to compare to.

        Returns:
            bool: True if blocks are equal, False otherwise.
        """
        res = True
        res = res and self.previous_hash == other.previous_hash
        res = res and self.hash() == other.hash()
        res = res and self.timestamp == other.timestamp
        res = res and self.nonce == other.nonce
        # Not necessary to check the transactions
        return res

    def hash(self):
        """
        Computes the SHA-256 hash of the block.

        Returns:
            str: Computed hash.
        """
        self.h = hashlib.sha256(str(self).encode()).hexdigest()
        return self.h

    def as_dict(self):
        """
        Returns a dictionary representation of the block.

        Returns:
            dict: Dictionary representation of the block.
        """
        block_dict = self.__dict__.copy()
        block_dict["merkle_tree"] = self.merkle_tree.as_dict()
        return block_dict

    def transactions(self):
        """
        Returns the list of transactions in the block.

        Returns:
            list: List of transactions.
        """
        return self.merkle_tree.transactions
