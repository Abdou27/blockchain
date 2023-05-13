import time
from Miner import Miner
from Wallet import Wallet

# Set up the nodes
miner_1 = Miner(node_name="Miner 1")
time.sleep(1)
wallet_1 = Wallet(known_nodes={miner_1.id()}, node_name="Wallet 1")
time.sleep(1)
miner_2 = Miner(known_nodes={miner_1.id()}, node_name="Miner 2")
time.sleep(1)
wallet_2 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 2")
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
