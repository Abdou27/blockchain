from Node import Node
from time import sleep

# Start up the nodes
n1 = Node(port=8000).listen()
sleep(1)
n2 = Node(port=8001, known_nodes={n1.id()}).listen()
sleep(1)
n3 = Node(port=8002, known_nodes={n1.id()}).listen()
sleep(1)

# Test that each node knows about the other two nodes
assert set(n1.known_nodes) == {n2.id(), n3.id()}
assert set(n2.known_nodes) == {n1.id(), n3.id()}
assert set(n3.known_nodes) == {n1.id(), n2.id()}
