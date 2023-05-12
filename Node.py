import json
import socket
import threading
import time
import hashlib


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
        return self

    def send(self, data, data_type, receiver=None, sender=None, data_hash=None, timestamp=None):
        if timestamp is None:
            timestamp = time.time_ns()
        if sender is None:
            sender = self.host, self.port
        payload_hash = hashlib.sha256(repr(
            (data_type, data, sender, receiver, timestamp)).encode()).hexdigest() if data_hash is None else data_hash
        self.hash_history.add(payload_hash)
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
            self.handle_incoming_transaction(payload, addr)
        elif data_type == "mined_block":
            self.handle_incoming_mined_block(payload, addr)
        else:
            pass

    def __repr__(self):
        return str((self.node_name, (self.host, self.port)))

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
