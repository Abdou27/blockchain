import hashlib
import threading

from Crypto.PublicKey import RSA
from Node import Node
from Transaction import Transaction


class Wallet(Node):
    def __init__(self, **options):
        super().__init__(**options)
        self.utxos = {}
        self.utxos_condition = threading.Condition()

    def _handle_incoming_data(self, payload, addr):
        super()._handle_incoming_data(payload, addr)

    def _handle_incoming_utxos_response(self, payload, addr):
        with self.utxos_condition:
            self.utxos = payload.get("data")
            self.utxos_condition.notify()

    def _request_utxos(self):
        self._send(self.address, 'utxos_request')

    def refresh_balance(self):
        with self.utxos_condition:
            self._request_utxos()
            self.utxos_condition.wait()

    def get_balance(self):
        total_input_value = 0
        for utxo_id, utxo in self.utxos.items():
            total_input_value += utxo["amount"]
        return total_input_value

    def send_crypto(self, receiver_address, amount):
        inputs = []
        outputs = []
        total_input_value = 0
        utxos_to_remove = []
        utxos_to_add = []

        for utxo_id, utxo in self.utxos.items():
            inputs.append({"transaction_hash": utxo_id.split(':')[0], "output_index": int(utxo_id.split(':')[1]),
                           "unlocking_script": None})
            total_input_value += utxo["amount"]
            utxos_to_remove.append(utxo_id)  # Add the used utxo_id to the used_utxos list

            if total_input_value >= amount:
                break

        # Check if the wallet has enough balance
        if total_input_value < amount:
            Node.print(f"Node {self.node_name} has insufficient balance.")
            return

        # Create outputs
        outputs.append({"amount": amount, "locking_script": self.generate_locking_script(receiver_address)})

        # If there's change, add another output for the change
        change = total_input_value - amount
        if change > 0:
            change_utxo = {"amount": change, "locking_script": self.generate_locking_script(self.address)}
            outputs.append(change_utxo)
            utxos_to_add.append(change_utxo)

        # Sign the inputs using the wallet's private key
        for tx_input in inputs:
            signature = Transaction.sign_transaction_input(self.private_key, tx_input['transaction_hash'],
                                                           tx_input['output_index'])
            tx_input['unlocking_script'] = self.generate_unlocking_script(tx_input['transaction_hash'],
                                                                          tx_input['output_index'], signature)

        # Create and send the transaction
        tx = self.create_transaction(inputs, outputs)

        # Remove used UTXOs from the wallet's utxos dictionary
        for utxo_id in utxos_to_remove:
            del self.utxos[utxo_id]

        for utxo in utxos_to_add:
            self.utxos[f"{tx.hash()}:1"] = utxo
