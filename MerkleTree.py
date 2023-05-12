import hashlib


class MerkleTree:
    def __init__(self, transactions=None):
        self.transactions = transactions or []
        self.tree = []

    def build_tree(self):
        self.tree = [self.transactions]
        while len(self.tree[-1]) > 1:
            nodes = []
            for i in range(0, len(self.tree[-1]), 2):
                left_node = self.tree[-1][i]
                right_node = self.tree[-1][i + 1] if (i + 1) < len(self.tree[-1]) else left_node
                nodes.append(self.hash_nodes(left_node, right_node))
            self.tree.append(nodes)

    def get_root(self):
        return self.tree[-1][0] if self.tree else None

    def update_tree(self, new_transactions):
        self.transactions.extend(new_transactions)
        self.build_tree()

    @staticmethod
    def hash_nodes(left, right):
        return hashlib.sha256((left + right).encode()).hexdigest()

    def verify_proof(self, tx_hash, proof):
        current_hash = tx_hash
        for node, side in proof:
            if side == "left":
                current_hash = self.hash_nodes(node, current_hash)
            else:
                current_hash = self.hash_nodes(current_hash, node)
        return current_hash == self.get_root()
