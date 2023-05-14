import hashlib
from Transaction import Transaction


class MerkleTreeNode:
    def __init__(self, h, level, left=None, right=None, parent=None):
        self.hash = h
        self.level = level
        self.left = left
        self.right = right
        self.parent = parent

    def is_leaf(self):
        return self.left is None and self.right is None

    def as_dict(self):
        node_dict = self.__dict__.copy()
        del node_dict['parent']
        node_dict['left'] = node_dict['left'].as_dict() if node_dict['left'] else None
        node_dict['right'] = node_dict['right'].as_dict() if node_dict['right'] else None


class MerkleTree:
    def __init__(self, transactions=None):
        self.transactions = list(map(lambda x: Transaction(x), transactions)) if transactions else []
        self.tree_root = None
        self.build_tree()

    def as_dict(self):
        return {
            'transactions': list(map(lambda x: x.as_dict(), self.transactions.copy())),
            'tree': self.tree_root.as_dict()
        }

    def build_tree(self):
        level = 0
        tree_leaves = [MerkleTreeNode(tx.hash(), level, None, None) for tx in self.transactions]

        # Build the tree by either creating a new node to hold two sub-nodes or using the lone node as is
        while len(tree_leaves) > 1:
            level += 1
            new_tree_leaves = []
            for i in range(0, len(tree_leaves), 2):
                if i < len(tree_leaves) - 1:
                    # Two sub-nodes
                    h = self.hash_nodes(tree_leaves[i].hash, tree_leaves[i + 1].hash)
                    new_tree_leaves.append(MerkleTreeNode(h, level, tree_leaves[i], tree_leaves[i + 1]))
                else:
                    # Lone node
                    new_tree_leaves.append(tree_leaves[i])
            tree_leaves = new_tree_leaves

        # The root node gives access to the whole tree
        self.tree_root = tree_leaves[0]

        # Walk the tree to set the parents
        self._set_parent(self.tree_root)

    def _set_parent(self, node):
        if node.left is not None:
            node.left.parent = node
            self._set_parent(node.left)
        if node.right is not None:
            node.right.parent = node
            self._set_parent(node.right)

    def get_root(self):
        return self.tree_root

    def update_tree(self, new_transactions):
        self.transactions.extend(list(map(lambda x: Transaction(x), new_transactions)) if new_transactions else [])
        self.tree_root = None
        self.build_tree()

    @staticmethod
    def hash_nodes(left, right):
        # To make the operation commutative (left + right == right + left),
        # we will convert both sides to integers
        left = int(left, 16)
        right = int(right, 16)
        return hashlib.sha256(str(left + right).encode()).hexdigest()

    def get_proof(self, tx_hash):
        proof = []
        node = self._find_node(self.tree_root, tx_hash)
        if node is None:
            return None

        current = node
        while current.level < self.tree_root.level:
            sibling = self._get_sibling(current)
            proof.append(sibling.hash)
            current = current.parent

        return proof

    def verify_proof(self, tx_hash, proof):
        current_hash = tx_hash
        for next_hash in proof:
            current_hash = self.hash_nodes(current_hash, next_hash)
        return current_hash == self.tree_root.hash

    def _find_node(self, node, tx_hash):
        if node is None:
            return None
        if node.is_leaf() and node.hash == tx_hash:
            return node

        left_result = self._find_node(node.left, tx_hash)
        right_result = self._find_node(node.right, tx_hash)

        return left_result if left_result else right_result

    @staticmethod
    def _get_sibling(node):
        parent = node.parent
        if parent is None:
            return None
        return parent.left if parent.right == node else parent.right