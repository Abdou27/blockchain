import json
import random
import socket
import threading
import time
import hashlib

from Block import Block
from Script import Script
from Transaction import Transaction


class Node:
    def __init__(self, **options):
        self.host = options.get("host", "127.0.0.1")
        self.port = options.get("port", 0)
        self.node_name = options.get("node_name", str((self.host, self.port)))
        self.max_listens = options.get("max_listens", 1024 ** 2)
        self.block_min_transactions = options.get("block_min_transactions", 5)
        self.max_recv_size = options.get("max_recv_size", 1024 ** 2)
        self.logging_level = options.get("logging_level", 1)
        self.debug_mode = options.get("debug_mode", False)
        self.outgoing_socket = None
        self.incoming_socket = None
        self.hash_history = []
        self.transactions = []
        self.blockchain = []
        self.known_nodes = options.get("known_nodes", set())
        self.lock = threading.Lock()
        self.listen()
        self.send((self.host, self.port), "new_node")

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
            threading.Thread(target=self.__accept_connections, daemon=True).start()
            # Add mining thread with a difficulty of 4
            threading.Thread(target=self.mine, args=(4,), daemon=True).start()
        return self

    def send(self, data, data_type, receiver=None, sender=None, data_hash=None, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        if sender is None:
            sender = self.host, self.port
        payload_hash = hashlib.sha256(repr(
            (data_type, data, sender, receiver, timestamp)).encode()).hexdigest() if data_hash is None else data_hash
        self.hash_history.append(payload_hash)
        payload = {"hash": payload_hash, "type": data_type, "sender": sender, "sent_at": timestamp,
                   "receiver": receiver, "data": data}
        payload = json.dumps(payload)
        payload = payload.encode()
        with self.lock:
            for known_node in self.known_nodes:
                self.__connect_and_send(known_node, payload)
                if self.logging_level >= 3:
                    Node.print(f"Node {self.node_name} sent payload to {known_node} : {payload}.")
                self.__disconnect()

    def mine(self, difficulty):
        while True:
            if len(self.transactions) >= self.block_min_transactions:
                previous_hash = self.blockchain[-1].hash() if len(self.blockchain) > 0 else "0" * 64
                new_block = Block(self.transactions, previous_hash)
                new_block.nonce = random.randint(0, 2**32)
                while not new_block.hash().startswith("0" * difficulty):
                    new_block.nonce += 1
                self.blockchain.append(new_block)
                self.transactions = []
                self.send(new_block, "mined_block")

    def __connect_and_send(self, node, payload):
        try:
            self.__connect(*node).send(payload)
        except Exception as e:
            Node.print(e)

    def __send_to_node(self, node, payload):
        with self.lock:
            self.__connect_and_send(node, payload)
            self.__disconnect()

    def __connect(self, host, port):
        self.outgoing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.outgoing_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.outgoing_socket.connect((host, port))
        if self.logging_level >= 2:
            Node.print(f"Node {self.node_name} is connected to {(host, port)}.")
        return self.outgoing_socket

    def __disconnect(self):
        self.outgoing_socket.shutdown(socket.SHUT_RDWR)
        self.outgoing_socket.close()
        if self.logging_level >= 2:
            Node.print(f"Node {self.node_name} is disconnected.")
        return self

    def __accept_connections(self):
        while True:
            conn, addr = self.incoming_socket.accept()
            if self.logging_level >= 1:
                Node.print(f"Node {self.node_name} accepted a connection from {addr}.")
            threading.Thread(target=self.__handle_conn, args=(conn, addr), daemon=True).start()

    def __handle_conn(self, conn, addr):
        with conn:
            data = conn.recv(self.max_recv_size).decode()
            threading.Thread(target=self.__handle_incoming_data, args=(data, addr)).start()

    def __handle_incoming_data(self, payload, addr):
        try:
            payload = json.loads(payload)
            if self.logging_level >= 1:
                Node.print(f"Node {self.node_name} received valid payload from {addr} : {payload}.")
        except ValueError:
            if self.logging_level >= 0:
                Node.print(f"Node {self.node_name} received invalid payload from {addr} : {payload}.")
        if payload["hash"] in self.hash_history:
            return
        data_type = payload.get("type")
        if data_type is None:
            pass
        elif data_type == "new_node":
            data = payload.get("data")
            if len(data) != 2:
                return
            data = tuple(data)
            with self.lock:
                self.known_nodes.add(data)
            self.send(list(self.known_nodes), "known_nodes")
        elif data_type == "known_nodes":
            data = payload.get("data")
            for n in data:
                if len(n) != 2 or (n[0], n[1]) == (self.host, self.port):
                    continue
                n = tuple(n)
                with self.lock:
                    self.known_nodes.add(n)
        elif data_type == "transaction":
            data = payload.get("data")
            transaction = Transaction(data["inputs"], data["outputs"])

            if Node.execute_transaction(transaction):
                self.transactions.append(transaction)
        elif data_type == "mined_block":
            data = payload.get("data")
            transactions, previous_hash, nonce = data
            block = Block(transactions, previous_hash)
            block.nonce = nonce
            self.blockchain.append(block)
        else:
            pass

    def __repr__(self):
        return str((self.node_name, (self.host, self.port)))

    @staticmethod
    def execute_transaction(transaction):
        for tx_input, tx_output in zip(transaction.inputs, transaction.outputs):
            unlocking_script = Script(tx_input["unlocking_script"])
            locking_script = Script(tx_output["locking_script"])
            stack = []

            if not unlocking_script.execute(stack) or not locking_script.execute(stack):
                return False

        return True

    @staticmethod
    def wait(*nodes):
        try:
            while True:
                time.sleep(60 * 60 * 24)  # 1 Day
        except KeyboardInterrupt:
            for node in nodes:
                with node.lock:
                    node.__disconnect()

    @staticmethod
    def print(text):
        print(str(text) + "\n", end="")
