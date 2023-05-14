import time
import random
import hashlib

from Miner import Miner
from Node import Node
from Block import Block
from Transaction import Transaction
from Script import Script
from MerkleTree import MerkleTree
from Wallet import Wallet

logging_level = 1


def test_exercise_1():
    print("Starting E1 tests :")
    print("Here we test if the nodes know about each other when connecting to the network.")

    # Start up the nodes
    n1 = Node(node_name="1", logging_level=logging_level)
    time.sleep(1)
    n2 = Node(node_name="2", known_nodes={n1.id()}, logging_level=logging_level)
    time.sleep(1)
    n3 = Node(node_name="3", known_nodes={n1.id()}, logging_level=logging_level)
    time.sleep(1)

    # Test that each node knows about the other two nodes
    assert set(n1.known_nodes) == {n2.id(), n3.id()}
    assert set(n2.known_nodes) == {n1.id(), n3.id()}
    assert set(n3.known_nodes) == {n1.id(), n2.id()}

    print("Passed E1 tests !")
    print(f"\n{'-'*20}")


def test_exercise_2():
    print("Starting E2 tests :")
    print("Here we test if the miners receive the transaction emitted by the wallet.")

    # Set up the nodes
    miner_1 = Miner(node_name="Miner 1", logging_level=logging_level)
    time.sleep(1)
    wallet = Wallet(known_nodes={miner_1.id()}, node_name="Wallet", logging_level=logging_level)
    time.sleep(1)
    miner_2 = Miner(known_nodes={miner_1.id()}, node_name="Miner 2", logging_level=logging_level)
    time.sleep(1)

    # Create an empty transactions
    wallet.create_transaction(inputs=[], outputs=[])

    # Give some time for the transaction to broadcast
    while True:
        time.sleep(1)
        if miner_1.transaction_pool == miner_2.transaction_pool:
            break
    assert len(miner_1.transaction_pool) == 1

    print("Passed E2 tests !")
    print(f"\n{'-'*20}")


def test_exercise_3():
    print("Starting E3 tests :")
    print("Here we test if the miners can mine a block and inform the others about it.")

    # Set up the nodes
    miner_1 = Miner(node_name="Miner 1", logging_level=logging_level)
    time.sleep(1)
    wallet_1 = Wallet(known_nodes={miner_1.id()}, node_name="Wallet 1", logging_level=logging_level)
    time.sleep(1)
    miner_2 = Miner(known_nodes={miner_1.id()}, node_name="Miner 2", logging_level=logging_level)
    time.sleep(1)
    wallet_2 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 2", logging_level=logging_level)
    time.sleep(1)

    # Create two empty transactions for the genesis block
    wallet_1.create_transaction(inputs=[], outputs=[])
    wallet_1.create_transaction(inputs=[], outputs=[])

    # Leave some time for mining
    while len(miner_1.blockchain) == 0:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 1

    # Create two other transactions
    wallet_2.create_transaction(inputs=[], outputs=[])
    wallet_2.create_transaction(inputs=[], outputs=[])

    # Leave some time for mining
    while len(miner_2.blockchain) == 1:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_2.blockchain) == 2

    print("Passed E3 tests !")
    print(f"\n{'-'*20}")


def test_exercise_4():
    print("Starting E4 tests :")
    print("Here we test if the transactions are properly processed.")

    # Set up the nodes
    miner_1 = Miner(node_name="Miner 1", logging_level=logging_level)
    time.sleep(1)
    wallet_1 = Wallet(known_nodes={miner_1.id()}, node_name="Wallet 1", logging_level=logging_level)
    time.sleep(1)
    miner_2 = Miner(known_nodes={miner_1.id()}, node_name="Miner 2", logging_level=logging_level)
    time.sleep(1)
    wallet_2 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 2", logging_level=logging_level)
    time.sleep(1)
    wallet_3 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 3", logging_level=logging_level)
    time.sleep(1)

    # Create two empty transactions for the genesis block
    wallet_1.create_transaction(inputs=[], outputs=[])
    wallet_1.create_transaction(inputs=[], outputs=[])

    # Leave some time for mining
    while len(miner_1.blockchain) == 0:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 1

    # One other empty transaction
    wallet_2.create_transaction(inputs=[], outputs=[])

    # Find the miner that mined the block
    for miner in [miner_1, miner_2]:
        utxo_id, utxo = list(miner.utxos.items())[0]
        if not utxo["locking_script"] == miner.generate_locking_script(miner.address):
            continue
        # This should be the second transaction in the second block
        miner.spend_mining_reward(wallet_1.address, utxo['amount'])

    # Leave some time for mining
    while len(miner_1.blockchain) == 1:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 2
    assert miner_1.utxos == miner_2.utxos

    # Check that wallet 1 received the mining reward
    wallet_1.refresh_balance()
    wallet_2.refresh_balance()
    wallet_3.refresh_balance()
    time.sleep(1)
    assert wallet_1.get_balance() == 50
    assert wallet_2.get_balance() == 0
    assert wallet_3.get_balance() == 0

    # Exchange crypto
    wallet_1.send_crypto(wallet_2.address, 20)
    wallet_1.send_crypto(wallet_3.address, 10)

    # Leave some time for mining
    while len(miner_1.blockchain) == 2:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 3
    assert miner_1.utxos == miner_2.utxos

    # Check that everyone has the amount they should have
    wallet_1.refresh_balance()
    wallet_2.refresh_balance()
    wallet_3.refresh_balance()
    time.sleep(1)
    assert wallet_1.get_balance() == 20
    assert wallet_2.get_balance() == 20
    assert wallet_3.get_balance() == 10

    print("Passed E4 tests !")
    print(f"\n{'-'*20}")


def test_exercise_5():
    print("Starting E5 tests :")
    print("Here we test if the merkle tree can provide valid proofs after a transaction.")

    # Set up the nodes
    miner_1 = Miner(node_name="Miner 1", logging_level=logging_level)
    time.sleep(1)
    wallet_1 = Wallet(known_nodes={miner_1.id()}, node_name="Wallet 1", logging_level=logging_level)
    time.sleep(1)
    miner_2 = Miner(known_nodes={miner_1.id()}, node_name="Miner 2", logging_level=logging_level)
    time.sleep(1)
    wallet_2 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 2", logging_level=logging_level)
    time.sleep(1)
    wallet_3 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 3", logging_level=logging_level)
    time.sleep(1)

    # Create two empty transactions for the genesis block
    wallet_1.create_transaction(inputs=[], outputs=[])
    wallet_1.create_transaction(inputs=[], outputs=[])

    # Leave some time for mining
    while len(miner_1.blockchain) == 0:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 1

    # One other empty transaction
    wallet_2.create_transaction(inputs=[], outputs=[])

    # Find the miner that mined the block
    for miner in [miner_1, miner_2]:
        utxo_id, utxo = list(miner.utxos.items())[0]
        if not utxo["locking_script"] == miner.generate_locking_script(miner.address):
            continue
        # This should be the second transaction in the second block
        miner.spend_mining_reward(wallet_1.address, utxo['amount'])

    # Leave some time for mining
    while len(miner_1.blockchain) == 1:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 2
    assert miner_1.utxos == miner_2.utxos

    # Check that wallet 1 received the mining reward
    wallet_1.refresh_balance()
    wallet_2.refresh_balance()
    wallet_3.refresh_balance()
    time.sleep(1)
    assert wallet_1.get_balance() == 50
    assert wallet_2.get_balance() == 0
    assert wallet_3.get_balance() == 0

    # Exchange crypto
    tx_to_check = wallet_1.send_crypto(wallet_2.address, 20)
    wallet_1.send_crypto(wallet_3.address, 10)

    # Leave some time for mining
    while len(miner_1.blockchain) == 2:
        time.sleep(1)

    # Check that both Miners have the same blockchain
    while not miner_1.blockchain == miner_2.blockchain:
        time.sleep(1)
    assert len(miner_1.blockchain) == 3
    assert miner_1.utxos == miner_2.utxos

    # Check that everyone has the amount they should have
    wallet_1.refresh_balance()
    wallet_2.refresh_balance()
    wallet_3.refresh_balance()
    time.sleep(1)
    assert wallet_1.get_balance() == 20
    assert wallet_2.get_balance() == 20
    assert wallet_3.get_balance() == 10

    # Create a Merkle Tree with some transactions
    merkle_tree = miner_1.blockchain[-1].merkle_tree

    # Get a Merkle Proof for one transaction
    tx_hash = tx_to_check.hash()
    proof = merkle_tree.get_proof(tx_hash)

    # Verify the proof
    assert merkle_tree.verify_proof(tx_hash, proof)

    print("Passed E5 tests !")
    print(f"\n{'-'*20}")


# Run the tests
test_exercise_1()
test_exercise_2()
test_exercise_3()
test_exercise_4()
test_exercise_5()

print("All tests passed.")
