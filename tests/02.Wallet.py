import time
from Miner import Miner
from Wallet import Wallet

# Set up the nodes
miner_1 = Miner(node_name="Miner 1")
time.sleep(1)
wallet = Wallet(known_nodes={miner_1.id()}, node_name="Wallet")
time.sleep(1)
miner_2 = Miner(known_nodes={miner_1.id()}, node_name="Miner 2")
time.sleep(1)

# Create an empty transactions
wallet.create_transaction(inputs=[], outputs=[])

# Give some time for the transaction to broadcast
while True:
    time.sleep(1)
    if miner_1.transaction_pool == miner_2.transaction_pool:
        break
assert len(miner_1.transaction_pool) == 1
