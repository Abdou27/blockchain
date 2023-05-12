import random
import time

from Node import Node

nodes = [Node(node_name="n1", logging_level=0).listen()]
n_nodes = 50
for i in range(2, n_nodes + 1):
    k = random.randint(1, 5)
    k = len(nodes) if k > len(nodes) else k
    choices = random.choices(nodes, k=k)
    known_nodes = set(map(lambda x: x.id(), choices))
    nodes.append(Node(node_name=f"n{i}", logging_level=0, known_nodes=known_nodes).listen())

time.sleep(10)

for node in nodes:
    print(len(node.known_nodes), ":", node.known_nodes)
pass
