import hashlib
import threading
import time

from Node import Node
from Block import Block
from Transaction import Transaction
import random


class Miner(Node):
    def __init__(self, **options):
        super().__init__(**options)
        self.block_min_transactions = options.get("block_min_transactions", 2)
        self.transactions = []
        self.blockchain = []
        # Add mining thread with a difficulty of 4
        threading.Thread(target=self.mine, args=(4,), daemon=True).start()

    def mine(self, difficulty):
        while True:
            if len(self.transactions) >= self.block_min_transactions:
                previous_hash = self.blockchain[-1].hash() if len(self.blockchain) > 0 else "0" * 64
                new_block = Block(self.transactions, previous_hash)
                new_block.nonce = random.randint(0, 2 ** 32)

                while not new_block.hash().startswith("0" * difficulty):
                    # Check if the transactions in the new_block are still in the miner's transactions list
                    if not all(tx in self.transactions for tx in new_block.transactions):
                        break

                    new_block.nonce += 1

                # If mining was successful, add the block to the blockchain and broadcast it
                if new_block.hash().startswith("0" * difficulty):
                    self.blockchain.append(new_block)
                    self.transactions = [tx for tx in self.transactions if tx not in new_block.transactions]
                    self.send(new_block.as_dict(), "mined_block")
                    Node.print(f"Node {self.node_name} successfully mined a block : {new_block.as_dict()}")

    def handle_incoming_transaction(self, payload, addr):
        data = payload.get("data")
        inputs, outputs, timestamp = data['inputs'], data['outputs'], data['timestamp']
        transaction = Transaction(inputs, outputs, timestamp)
        if transaction.execute():
            self.transactions.append(transaction)

    def handle_incoming_mined_block(self, payload, addr):
        data = payload.get("data")
        transactions, previous_hash, nonce = data['transactions'], data['previous_hash'], data['nonce']
        timestamp = data['timestamp']
        transactions = list(map(lambda x: Transaction(x['inputs'], x['outputs'], x['timestamp']), transactions))
        block = Block(transactions, previous_hash, nonce=nonce, timestamp=timestamp)

        # Check if the received block's transactions are in the miner's current transaction list
        for tx in transactions:
            if tx in self.transactions:
                self.transactions.remove(tx)

        self.blockchain.append(block)

    def handle_incoming_mined_block(self, payload, addr):
        data = payload.get("data")
        transactions, previous_hash, nonce, timestamp = data['transactions'], data['previous_hash'], data['nonce'], data['timestamp']
        transactions = list(map(lambda x: Transaction(x['inputs'], x['outputs'], x['timestamp']), transactions))
        block = Block(transactions, previous_hash, nonce=nonce, timestamp=timestamp)
        self.blockchain.append(block)
