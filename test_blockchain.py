import time
import random
import hashlib
from Node import Node
from Block import Block
from Transaction import Transaction
from Script import Script
from MerkleTree import MerkleTree


def test_exercise_1():
    node1 = Node(node_name="Node1")
    time.sleep(1)
    node2 = Node(known_nodes={node1.id()}, node_name="Node2")
    time.sleep(1)

    assert node1.known_nodes == {node2.id()}
    assert node2.known_nodes == {node1.id()}


def test_exercise_2():
    # Set up the nodes
    node1 = Node(node_name="Node1")
    time.sleep(1)
    node2 = Node(known_nodes={node1.id()}, node_name="Node2")
    time.sleep(1)

    # Create a sample transaction
    tx = Transaction(
        inputs=[{"unlocking_script": "OP_DUP OP_HASH160"}],
        outputs=[{"locking_script": "OP_DUP OP_HASH160 OP_EQUALVERIFY"}]
    )
    node1._send(tx, "transaction")

    # Give some time for the transaction to broadcast
    time.sleep(1)

    assert tx in node2.transactions


def test_exercise_3():
    # Set up the nodes
    node1 = Node(node_name="Node1")
    time.sleep(1)
    node2 = Node(known_nodes={node1.id()}, node_name="Node2")
    time.sleep(1)

    # Create sample transactions and broadcast them
    for _ in range(5):
        tx = Transaction(
            inputs=[{"unlocking_script": "OP_DUP OP_HASH160"}],
            outputs=[{"locking_script": "OP_DUP OP_HASH160 OP_EQUALVERIFY"}]
        )
        node1._send(tx, "transaction")
        time.sleep(0.5)

    # Give some time for mining and broadcasting
    time.sleep(10)

    assert len(node1.blockchain) == 1
    assert len(node2.blockchain) == 1
    assert node1.blockchain[0].hash() == node2.blockchain[0].hash()


def test_exercise_4():
    unlocking_script = "OP_DUPOP_HASH160"
    locking_script = "OP_DUP OP_HASH160 OP_EQUALVERIFY"
    stack = []

    tx_input = {"unlocking_script": unlocking_script}
    tx_output = {"locking_script": locking_script}

    transaction = Transaction([tx_input], [tx_output])

    assert Node.execute_transaction(transaction)


def test_exercise_5():
    # Create a Merkle Tree with some transactions
    transactions = [hashlib.sha256(str(i).encode()).hexdigest() for i in range(5)]
    merkle_tree = MerkleTree(transactions)
    merkle_tree.build_tree()

    # Get a Merkle Proof for one transaction
    tx_index = 2
    tx_hash = transactions[tx_index]
    proof = merkle_tree.get_proof(tx_index)

    # Verify the proof
    assert merkle_tree.verify_proof(tx_hash, proof)


# Run the tests
test_exercise_1()
test_exercise_2()
test_exercise_3()
test_exercise_4()
test_exercise_5()

print("All tests passed.")
