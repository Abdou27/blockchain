import hashlib
import threading
import time

from Node import Node
from Block import Block
from Transaction import Transaction
import random


class Miner(Node):
    def __init__(self, **options):
        """
        Constructs a new Miner object.

        :param **options: optional parameters to configure the Miner object.
        """
        super().__init__(**options)
        self.block_min_transactions = options.get("block_min_transactions", 2)
        self.stop_mining = False
        self.transaction_pool = []
        self.blockchain = []
        self.utxos = {}
        # Add mining thread with a difficulty of 4
        threading.Thread(target=self._mine, args=(4,), daemon=True).start()

    def _mine(self, difficulty):
        """
        A private method that performs the actual mining process.

        :param difficulty: the difficulty level of the mining process.
        """
        while True:
            if not self.stop_mining and len(self.transaction_pool) >= self.block_min_transactions:

                previous_hash = self.blockchain[-1].hash() if len(self.blockchain) > 0 else "0" * 64
                new_block = Block(len(self.blockchain), self.transaction_pool, previous_hash)
                new_block.nonce = random.randint(0, 2 ** 32)
                # Create a coinbase transaction for the mining reward
                transaction_fee = 50
                coinbase_transaction = self._create_reward_transaction(transaction_fee)
                new_block.merkle_tree.transactions.insert(0, coinbase_transaction)
                new_block.merkle_tree.build_tree()

                while not new_block.hash().startswith("0" * difficulty):
                    # Check if the transactions in the new_block are still in the miner's transactions list
                    if self.stop_mining or not all(tx in self.transaction_pool for tx in
                               new_block.merkle_tree.transactions[1:]):  # Skip the coinbase transaction
                        break
                    new_block.nonce += 1

                if new_block.hash().startswith("0" * difficulty):
                    # Add the mined block to the blockchain and broadcast it
                    self.blockchain.append(new_block)
                    self._update_utxos_from_blockchain()
                    self.transaction_pool = [tx for tx in self.transaction_pool if
                                             tx not in new_block.merkle_tree.transactions[1:]]
                    Node.print(f"Node {self.node_name} successfully mined a block : {new_block.as_dict()}")
                    self._send(new_block.as_dict(), "mined_block")

            time.sleep(1)

    def _create_reward_transaction(self, reward_amount):
        """
        A private method that creates a coinbase transaction with a given reward amount.

        :param reward_amount: the amount of the mining reward to be included in the coinbase transaction.
        :return: the coinbase transaction.
        """
        # Create a coinbase transaction with no inputs and an output that transfers the reward to the miner's address
        coinbase_transaction = Transaction({
            'inputs': [],
            'outputs': [{
                'amount': reward_amount,
                'locking_script': self.generate_locking_script(self.address)
            }]
        })

        return coinbase_transaction

    def _handle_incoming_data(self, payload, addr):
        """
        An override of the `_handle_incoming_data` method of the Node class.
        Handles incoming data from other nodes.

        :param payload: the data payload received from other nodes.
        :param addr: the address of the sender node.
        """
        super()._handle_incoming_data(payload, addr)

    def _handle_incoming_transaction(self, payload, addr):
        """
        An override of the `_handle_incoming_transaction` method of the Node class.
        Handles incoming transactions from other nodes.

        :param payload: the transaction payload received from other nodes.
        :param addr: the address of the sender node.
        """
        data = payload.get("data")
        transaction = Transaction(data)
        if transaction.execute():
            self.transaction_pool.append(transaction)

    def _handle_incoming_mined_block(self, payload, addr):
        """
        An override of the `_handle_incoming_mined_block` method of the Node class.
        Handles incoming mined blocks from other nodes.

        :param payload: the mined block payload received from other nodes.
        :param addr: the address of the sender node.
        """
        data = payload.get("data")
        index, timestamp, previous_hash, nonce = data['index'], data['timestamp'], data['previous_hash'], data['nonce']
        transactions = data['merkle_tree']['transactions']
        block = Block(index, transactions, previous_hash, nonce=nonce, timestamp=timestamp)

        # Check if the received block is valid
        if self._is_valid_block(block):
            self.stop_mining = True

            # Update UTXOs
            for tx in block.merkle_tree.transactions:
                tx_hash = tx.hash()
                for i, tx_output in enumerate(tx.outputs):
                    self.utxos[f"{tx_hash}:{i}"] = tx_output

                for tx_input in tx.inputs:
                    utxo_id = f"{tx_input['transaction_hash']}:{tx_input['output_index']}"
                    if utxo_id in self.utxos:
                        del self.utxos[utxo_id]

            # Check if the received block's transactions are in the miner's current transaction list
            for tx in transactions:
                if tx in self.transaction_pool:
                    self.transaction_pool.remove(tx)

            # Add the block to the blockchain
            self.blockchain.append(block)
            self._update_utxos_from_blockchain()
            self.stop_mining = False
        elif block.index >= len(self.blockchain):
            # This block is ahead of the current block, request an update
            self.request_blockchain_update()
        else:
            # This block is invalid because the current blockchain has already surpassed it, do nothing
            pass

    def _handle_incoming_blockchain_request(self, payload, addr):
        """
        An override of the `_handle_incoming_blockchain_request` method of the Node class.
        Handles incoming blockchain update requests from other nodes.

        :param payload: the blockchain request payload received from other nodes.
        :param addr: the address of the sender node.
        """
        # Send the current blockchain to the requesting node
        serialized_blockchain = [block.as_dict() for block in self.blockchain]
        self._send(serialized_blockchain, "blockchain_update", receiver=payload["sender"])

    def _handle_incoming_blockchain_update(self, payload, addr):
        """
        An override of the `_handle_incoming_blockchain_update` method of the Node class.
        Handles incoming blockchain updates from other nodes.

        :param payload: the blockchain update payload received from other nodes.
        :param addr: the address of the sender node.
        """
        data = payload.get("data")
        received_blockchain = [Block(block['index'], block["merkle_tree"]["transactions"], block["previous_hash"],
                                     nonce=block["nonce"], timestamp=block["timestamp"]) for block in data]

        # Compare the length of the received blockchain with the local blockchain
        if len(received_blockchain) > len(self.blockchain):
            # If the received blockchain is longer, update the local blockchain
            self.blockchain = received_blockchain
            self._update_utxos_from_blockchain()

    def _handle_incoming_utxos_request(self, payload, addr):
        """
        A private method that handles incoming UTXO requests from a wallet.

        :param payload: the UTXO request payload received from a wallet.
        :param addr: the address of the sender node.
        """
        address = payload.get("data")
        # Find the UTXOs that belong to the miner and have not been spent
        utxos = {utxo_id: utxo for utxo_id, utxo in self.utxos.items() if
                           utxo["locking_script"] == self.generate_locking_script(address)}
        self._send(utxos, 'utxos_response', receiver=tuple(payload.get('sender')))

    def _is_valid_block(self, block):
        """
        Check if a block is valid with the current blockchain.

        :param block: the block to check
        :return: bool: whether the block is valid or not
        """
        # Check if the block's previous hash matches the hash of the last block in the current blockchain
        if len(self.blockchain) > 0 and block.previous_hash != self.blockchain[-1].hash():
            return False

        # Validate the proof-of-work by checking if the block's hash starts with the required number of zeros
        difficulty = 4
        if not block.hash().startswith("0" * difficulty):
            return False

        return True

    def request_blockchain_update(self):
        """
        Broadcasts a request for the latest blockchain to all connected miners.

        :return: None
        """
        # Broadcast a request for the latest blockchain
        self._send(self.id(), "request_blockchain")
        Node.print(f"Node {self.node_name} made a blockchain update request.")

    def _update_utxos_from_blockchain(self):
        """
        Clears the current UTXOs and rebuilds them from the updated blockchain.

        :return: None
        """
        # Clear the current UTXOs and rebuild them from the updated blockchain
        self.utxos = {}
        for block in self.blockchain:
            for tx in block.merkle_tree.transactions:
                tx_hash = tx.hash()
                for i, tx_output in enumerate(tx.outputs):
                    self.utxos[f"{tx_hash}:{i}"] = tx_output

                for tx_input in tx.inputs:
                    utxo_id = f"{tx_input['transaction_hash']}:{tx_input['output_index']}"
                    if utxo_id in self.utxos:
                        del self.utxos[utxo_id]

    def spend_mining_reward(self, receiver_address, amount):
        """
        Creates a new transaction using the available UTXOs and sends the desired amount to the receiver's address.

        :param receiver_address: The address of the receiver.
        :type receiver_address: str
        :param amount: The amount to be sent.
        :type amount: float
        :return: None
        """
        # Find the UTXOs that belong to the miner and have not been spent
        available_utxos = {utxo_id: utxo for utxo_id, utxo in self.utxos.items() if
                           utxo["locking_script"] == self.generate_locking_script(self.address)}

        # Create a new transaction using the available UTXOs and send the desired amount to the receiver's address
        inputs = []
        outputs = []
        total_input_value = 0

        for utxo_id, utxo in available_utxos.items():
            inputs.append({
                "transaction_hash": utxo_id.split(':')[0],
                "output_index": int(utxo_id.split(':')[1]),
                "unlocking_script": None
            })
            total_input_value += utxo["amount"]

            if total_input_value >= amount:
                break

        if total_input_value < amount:
            Node.print(f"Node {self.node_name} has insufficient balance.")
            return

        outputs.append({
            "amount": amount,
            "locking_script": self.generate_locking_script(receiver_address)
        })

        change = total_input_value - amount
        if change > 0:
            outputs.append({
                "amount": change,
                "locking_script": self.generate_locking_script(self.address)
            })

        for tx_input in inputs:
            signature = Transaction.sign_transaction_input(self.private_key, tx_input['transaction_hash'],
                                                           tx_input['output_index'])
            tx_input['unlocking_script'] = self.generate_unlocking_script(tx_input['transaction_hash'],
                                                                          tx_input['output_index'], signature)

        return self.create_transaction(inputs, outputs)
