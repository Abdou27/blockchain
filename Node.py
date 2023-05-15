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
        """
        Initializes a Node object with the given options.
        Generates a key pair for the node and creates an address from the public key.
        Starts listening on the given port and accepts incoming connections.
        Sends a "new_node" message to all known nodes.

        :param options: dict: include host, port, node_name, max_listens, max_recv_size, logging_level, known_nodes.
        """
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
        """
        Returns the id of the node, which is a tuple containing the host and port.

        :return: tuple
        """
        return self.host, self.port

    def listen(self):
        """
        Starts listening on the node's incoming socket and accepts incoming connections.

        :return: Node: the Node object
        """
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

    def _send(self, data, data_type, receiver=None, sender=None, sender_name=None, data_hash=None, timestamp=None):
        """
        Constructs a payload from the given data, data_type, sender, receiver, data_hash, and timestamp.
        Calculates the hash of the payload and adds it to the hash_history set.
        Sends the payload to all known nodes by connecting to each node, sending the payload, and then disconnecting.

        :param data: data to send
        :param data_type: type of message
        :param receiver: if specified, the receiving nodes will ignore the message if they're not the receiver
        :param sender: original sender of the message
        :param data_hash: hash of the data to send
        :param timestamp: timestamp in nanoseconds since the Epoch
        :return:
        """
        if timestamp is None:
            timestamp = time.time_ns()
        if sender is None:
            sender = self.id()
            sender_name = self.node_name
        payload_repr = repr((data_type, data, sender, sender_name, receiver, timestamp))
        payload_hash = hashlib.sha256(payload_repr.encode()).hexdigest() if data_hash is None else data_hash
        self.hash_history.add(payload_hash)
        payload = {"hash": payload_hash, "type": data_type, "sender": sender, "sender_name": sender_name,
                   "sent_at": timestamp, "receiver": receiver, "data": data}
        payload = json.dumps(payload)
        payload = payload.encode()
        with self.lock:
            for known_node in self.known_nodes:
                self._connect_and_send(known_node, payload)
                if self.logging_level >= 3:
                    Node.print(f"Node {self.node_name} sent payload to {known_node} : {payload}.")
                self._disconnect()

    def _connect_and_send(self, node, payload):
        """
        Connects to the given node, sends the given payload, and then disconnects.

        :param node: tuple: node to connect to
        :param payload: encoded data to send
        """
        try:
            self._connect(*node).send(payload)
        except Exception as e:
            Node.print(e)

    def _connect(self, host, port):
        """
        Connects to the given host and port.
        Returns the outgoing socket.

        :param host: str: host to connect to
        :param port: int: port to connect to
        :return: socket: the outgoing socket
        """
        self.outgoing_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.outgoing_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.outgoing_socket.connect((host, port))
        if self.logging_level >= 3:
            Node.print(f"Node {self.node_name} is connected to {(host, port)}.")
        return self.outgoing_socket

    def _disconnect(self):
        """
        Shuts down the outgoing socket and then disconnects.
        Returns the Node object.
        :return: Node
        """
        self.outgoing_socket.shutdown(socket.SHUT_RDWR)
        self.outgoing_socket.close()
        if self.logging_level >= 3:
            Node.print(f"Node {self.node_name} is disconnected.")
        return self

    def _accept_connections(self):
        """
        Accepts incoming connections on the node's incoming socket.

        Starts a new thread to handle each incoming connection.
        """
        while True:
            conn, addr = self.incoming_socket.accept()
            if self.logging_level >= 3:
                Node.print(f"Node {self.node_name} accepted a connection from {addr}.")
            threading.Thread(target=self._handle_conn, args=(conn, addr), daemon=True).start()

    def _handle_conn(self, conn, addr):
        """
        Receives data on the given connection and starts a new thread to handle the incoming data.

        :param conn: socket connection
        :param addr: address of the sending socket
        """
        with conn:
            data = conn.recv(self.max_recv_size).decode()
            threading.Thread(target=self._handle_incoming_data, args=(data, addr)).start()

    def _handle_incoming_data(self, payload, addr):
        """
        Handles incoming data from other nodes in the network.

        :param payload: str - the data payload received from the sender node
        :param addr: tuple - the IP address and port of the sender node
        """
        try:
            # Parse payload as a JSON object
            payload = json.loads(payload)
            # Extract relevant data from payload
            data_type = payload.get("type")
            sender = payload.get("sender")
            sender_name = payload.get("sender_name")
            receiver = payload.get("receiver")
            data_hash = payload.get("hash")
            timestamp = payload.get("sent_at")
            data = payload.get("data")
            # Check if the data has already been processed by the current node
            if data_hash in self.hash_history:
                return
            # Add data hash to hash history set to prevent processing duplicates
            self.hash_history.add(data_hash)
            # Check if data is intended for another node in the network, and forward it accordingly
            if receiver is not None and tuple(receiver) != self.id():
                self._send(data, data_type, receiver=tuple(receiver), sender=tuple(sender), sender_name=sender_name,
                           data_hash=data_hash, timestamp=timestamp)
                return
            if self.logging_level >= 2:
                Node.print(f"Node {self.node_name} received valid payload from {addr} : {payload}.")
        except ValueError:
            # Log error if incoming data cannot be parsed as JSON
            if self.logging_level >= 0:
                Node.print(f"Node {self.node_name} received invalid payload from {addr} : {payload}.")
            return

        # Call appropriate handler method based on the data type
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
            # Do nothing if the data type is not recognized
            pass

    def _handle_incoming_new_node(self, payload, addr):
        """
        Handle incoming "new_node" payload by adding the new node to the known_nodes set and broadcasting the updated
        set to all known nodes.

        :param payload: dict: The incoming payload from the new node.
        :param addr: tuple: The address (IP, port) of the node that sent the payload.
        """
        data = payload.get("data")
        if len(data) != 2:
            return
        data = tuple(data)
        with self.lock:
            self.known_nodes.add(data)
        self._send(list(self.known_nodes), "known_nodes")

    def _handle_incoming_known_nodes(self, payload, addr):
        """
        Handles incoming "known_nodes" payload received from other nodes in the network.

        :param payload: dict, the payload received from other nodes containing the list of known nodes.
        :param addr: tuple, the IP address and port number of the node sending the payload.
        """
        data = payload.get("data")
        for n in data:
            if len(n) != 2 or (n[0], n[1]) == (self.host, self.port):
                continue
            n = tuple(n)
            with self.lock:
                self.known_nodes.add(n)

    def _handle_incoming_transaction(self, payload, addr):
        """
        This method is a callback function that is called whenever a new transaction is received from another node in
        the network.
        """
        pass

    def _handle_incoming_mined_block(self, payload, addr):
        """
        This method is a callback function that is called whenever a new block is mined by a Miner in the network.
        """
        pass

    def _handle_incoming_blockchain_request(self, payload, addr):
        """
        This method is a callback function that is called whenever another node in the network requests the current
        node's copy of the blockchain.
        """
        pass

    def _handle_incoming_blockchain_update(self, payload, addr):
        """
        This method is a callback function that is called whenever another node in the network sends an updated version
        of the blockchain.
        """
        pass

    def _handle_incoming_utxos_request(self, payload, addr):
        """
        This method is a callback function that is called whenever a wallet in the network requests the current node's
        copy of the unspent transaction outputs (UTXOs).
        """
        pass

    def _handle_incoming_utxos_response(self, payload, addr):
        """
        This method is a callback function that is called whenever a Miner in the network sends its copy of the
        UTXOs in response to a request.
        """
        pass

    def create_transaction(self, inputs, outputs):
        """
        Creates a transaction and sends it to other nodes for processing.

        Args:
            inputs (list): List of tuples representing the inputs of the transaction.
            outputs (list): List of tuples representing the outputs of the transaction.

        Returns:
            transaction (Transaction): The created transaction object.
        """
        transaction = Transaction({
            'inputs': inputs,
            'outputs': outputs,
        })
        self._send(transaction.as_dict(), "transaction")
        Node.print(f"Node {self.node_name} sent a transaction : {transaction.as_dict()}")
        return transaction

    def __repr__(self):
        """
        Returns a string representation of the Node object.

        Returns:
            str: A string representation of the Node object.
        """
        return str((self.node_name, (self.host, self.port)))

    @staticmethod
    def generate_locking_script(address):
        """
        Generates the locking script for a given address.

        Args:
            address (str): The address for which the locking script is to be generated.

        Returns:
            list: A list representing the locking script for the given address.
        """
        return [address, "OP_EQUAL"]

    @staticmethod
    def generate_unlocking_script(transaction_hash, output_index, signature):
        """
        Generates the unlocking script for a given transaction hash, output index, and signature.

        Args:
            transaction_hash (str): The hash of the transaction being unlocked.
            output_index (int): The index of the output being unlocked.
            signature (bytes): The signature used to unlock the output.

        Returns:
            list: A list representing the unlocking script for the given transaction hash, output index, and signature.
        """
        # Convert the signature to a base64 string
        signature_str = base64.b64encode(signature).decode()
        return [signature_str, f"{transaction_hash}:{output_index}"]

    @staticmethod
    def generate_key_pair():
        """
        Generates a pair of RSA keys (private and public).
        Returns:
            private_key: object: RSA private key object.
            public_key: object: RSA public key object.
        """
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        return private_key, public_key

    @staticmethod
    def generate_address(public_key):
        """
        Generates a public address from a given public key using SHA256 hash.
        Args:
            public_key: object: RSA public key object.
        Returns:
            str: Public address string.
        """
        return hashlib.sha256(public_key.export_key(format='DER')).hexdigest()

    @staticmethod
    def wait(*nodes):
        """
        A utility function that puts the program on hold indefinitely.
        It waits for a KeyboardInterrupt exception, which is raised when the user terminates the program.
        Args:
            *nodes: List: An arbitrary number of node objects to disconnect on program termination.
        """
        try:
            while True:
                time.sleep(60 * 60 * 24)  # 1 Day
        except KeyboardInterrupt:
            for node in nodes:
                with node.lock:
                    node._disconnect()

    @staticmethod
    def print(text):
        """
        A utility function to print the given text without interlacing due to threads printing at the same time.
        Args:
            text: str: Text to print.
        """
        print(str(text) + "\n", end="")
