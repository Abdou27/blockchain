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
wallet_3 = Wallet(known_nodes={miner_2.id()}, node_name="Wallet 3")
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
