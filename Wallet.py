from Node import Node
from Transaction import Transaction


class Wallet(Node):
    def __init__(self, **options):
        super().__init__(**options)

    def create_transaction(self, inputs, outputs):
        transaction = Transaction(inputs, outputs)
        self.send(transaction.__dict__, "transaction")

    def process_payload(self, payload, addr):
        pass  # Wallets do not process incoming payloads in this example

    def handle_incoming_transaction(self, payload, addr):
        pass

    def handle_incoming_mined_block(self, payload, addr):
        pass
