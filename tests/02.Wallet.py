import time
from Miner import Miner
from Wallet import Wallet
from Node import Node
from Transaction import Transaction

# Set up the nodes

n1 = Miner(node_name="Miner 1")
time.sleep(1)
n2 = Wallet(known_nodes={n1.id()}, node_name="Wallet")
time.sleep(1)
n3 = Miner(known_nodes={n1.id()}, node_name="Miner 2")
time.sleep(1)

# Create two empty transactions
n2.create_transaction(inputs=[], outputs=[])

# Give some time for the transaction to broadcast
time.sleep(1)
assert len(n1.transactions) == 1
assert n1.transactions == n3.transactions
