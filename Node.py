import base64
import json
import socket
import threading
import time
import hashlib

from Crypto.PublicKey import RSA

from Transaction import Transaction


class Node:
    def __init__(self, **options):
        self.host = options.get("host", "127.0.0.1")
        self.port = options.get("port", 0)
        self.node_name = options.get("node_name", str((self.host, self.port)))
        self.max_listens = options.get("max_listens", 1024 ** 2)
        self.max_recv_size = options.get("max_recv_size", 1024 ** 2)
        self.logging_level = options.get("logging_level", 1)
        self.outgoing_socket = None
        self.incoming_socket = None
        self.hash_history = set()
        self.known_nodes = options.get("known_nodes", set())
        self.private_key, self.public_key = self.generate_key_pair()
        self.address = self.generate_address(self.public_key)
        self.lock = threading.Lock()
        self.listen()
        self._send((self.host, self.port), "new_node")

    def id(self):
        return self.host, self.port

    def listen(self):
        with self.lock:
            self.incoming_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.incoming_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.incoming_socket.bind((self.host, self.port))
            self.port = self.incoming_socket.getsockname()[1]
            self.incoming_socket.listen(self.max_listens)
            if self.logging_level >= 1:
                Node.print(f"Node {self.node_name} is listening on {self.incoming_socket.getsockname()}.")
            threading.Thread(target=self._accept_connections, daemon=True).start()
        return self

    def _send(self, data, data_type, receiver=None, sender=None, data_hash=None, timestamp=None):
        if timestamp is None:
            timestamp = time.time_ns()
        if sender is None:
            sender = self.id()
        payload_hash = hashlib.sha256(repr(
            (data_type, data, sender, receiver, timestamp)).encode()).hexdigest() if data_hash is None else data_hash
        self.hash_history.add(payload_hash)
        payload = {"hash": payload_hash, "type": data_type, "sender": sender, "sent_at": timestamp,
                   "receiver": receiver, "data": data}
        payload = json.dumps(payload)
        payload = payload.encode()
        with self.lock:
            for known_node in self.known_nodes:
                self._connect_and_send(known_node, payload)
                if self.logging_level >= 3:
                    Node.print(f"Node {self.node_name} sent payload to {known_node} : {payload}.")
                self._disconnect()

    def _connect_and_send(self, node, payload):
        try:
            self._connect(*node).send(payload)
        except Exception as e:
            Node.print(e)

    def _send_to_node(self, node, payload):
        with self.lock:
            self._connect_and_send(node, payload)
            self._disconnect()

    def _connect(self, host, port):
        self.outgoing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.outgoing_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.outgoing_socket.connect((host, port))
        if self.logging_level >= 3:
            Node.print(f"Node {self.node_name} is connected to {(host, port)}.")
        return self.outgoing_socket

    def _disconnect(self):
        self.outgoing_socket.shutdown(socket.SHUT_RDWR)
        self.outgoing_socket.close()
        if self.logging_level >= 3:
            Node.print(f"Node {self.node_name} is disconnected.")
        return self

    def _accept_connections(self):
        while True:
            conn, addr = self.incoming_socket.accept()
            if self.logging_level >= 3:
                Node.print(f"Node {self.node_name} accepted a connection from {addr}.")
            threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()

    def _handle_conn(self, conn, addr):
        with conn:
            data = conn.recv(self.max_recv_size).decode()
            threading.Thread(target=self._handle_incoming_data, args=(data, addr)).start()

    def _handle_incoming_data(self, payload, addr):
        try:
            payload = json.loads(payload)
            data_type = payload.get("type")
            sender = payload.get("sender")
            receiver = payload.get("receiver")
            data_hash = payload.get("hash")
            timestamp = payload.get("sent_at")
            data = payload.get("data")
            if data_hash in self.hash_history:
                return
            self.hash_history.add(data_hash)
            if receiver is not None and tuple(receiver) != self.id():
                self._send(data, data_type, receiver=tuple(receiver), sender=tuple(sender), data_hash=data_hash,
                           timestamp=timestamp)
                return
            if self.logging_level >= 2:
                Node.print(f"Node {self.node_name} received valid payload from {addr} : {payload}.")
        except ValueError:
            if self.logging_level >= 0:
                Node.print(f"Node {self.node_name} received invalid payload from {addr} : {payload}.")
            return

        if data_type == "new_node":
            self._handle_incoming_new_node(payload, addr)
        elif data_type == "known_nodes":
            self._handle_incoming_known_nodes(payload, addr)
        elif data_type == "transaction":
            self._handle_incoming_transaction(payload, addr)
        elif data_type == "mined_block":
            self._handle_incoming_mined_block(payload, addr)
        elif data_type == "request_blockchain":
            self._handle_incoming_blockchain_request(payload, addr)
        elif data_type == "blockchain_update":
            self._handle_incoming_blockchain_update(payload, addr)
        elif data_type == "utxos_request":
            self._handle_incoming_utxos_request(payload, addr)
        elif data_type == "utxos_response":
            self._handle_incoming_utxos_response(payload, addr)
        else:
            pass

    def _handle_incoming_new_node(self, payload, addr):
        data = payload.get("data")
        if len(data) != 2:
            return
        data = tuple(data)
        with self.lock:
            self.known_nodes.add(data)
        self._send(list(self.known_nodes), "known_nodes")

    def _handle_incoming_known_nodes(self, payload, addr):
        data = payload.get("data")
        for n in data:
            if len(n) != 2 or (n[0], n[1]) == (self.host, self.port):
                continue
            n = tuple(n)
            with self.lock:
                self.known_nodes.add(n)

    def _handle_incoming_transaction(self, payload, addr):
        pass

    def _handle_incoming_mined_block(self, payload, addr):
        pass

    def _handle_incoming_blockchain_request(self, payload, addr):
        pass

    def _handle_incoming_blockchain_update(self, payload, addr):
        pass

    def _handle_incoming_utxos_request(self, payload, addr):
        pass

    def _handle_incoming_utxos_response(self, payload, addr):
        pass

    def create_transaction(self, inputs, outputs):
        transaction = Transaction({
            'inputs': inputs,
            'outputs': outputs,
        })
        self._send(transaction.as_dict(), "transaction")
        Node.print(f"Node {self.node_name} sent a transaction : {transaction.as_dict()}")
        return transaction

    def __repr__(self):
        return str((self.node_name, (self.host, self.port)))

    @staticmethod
    def generate_locking_script(address):
        return [address, "OP_EQUAL"]

    @staticmethod
    def generate_unlocking_script(transaction_hash, output_index, signature):
        # Convert the signature to a base64 string
        signature_str = base64.b64encode(signature).decode()
        return [signature_str, f"{transaction_hash}:{output_index}"]

    @staticmethod
    def generate_key_pair():
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        return private_key, public_key

    @staticmethod
    def generate_address(public_key):
        return hashlib.sha256(public_key.export_key(format='DER')).hexdigest()

    @staticmethod
    def wait(*nodes):
        try:
            while True:
                time.sleep(60 * 60 * 24)  # 1 Day
        except KeyboardInterrupt:
            for node in nodes:
                with node.lock:
                    node._disconnect()

    @staticmethod
    def print(text):
        print(str(text) + "\n", end="")
