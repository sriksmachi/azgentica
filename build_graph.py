import json
import networkx as nx
import matplotlib.pyplot as plt


def create_architecture_graph(architecture_json):
    """
    Create a directed graph from the architecture JSON data.

    Args:
        architecture_json (dict): The architecture data in JSON format.

    Returns:
        nx.DiGraph: A directed graph representing the architecture.
    """
    # Initialize a directed graph
    G = nx.DiGraph()

    # Add nodes to the graph
    for node in architecture_json["nodes"]:
        G.add_node(node["id"], label=node["label"], type=node["type"])

    # Add edges to the graph
    for edge in architecture_json["edges"]:
        G.add_edge(edge["source"], edge["target"], label=edge["label"])

    return G


def draw_graph(G):
    """
    Draw the directed graph using matplotlib.

    Args:
        G (nx.DiGraph): The directed graph to draw.
    """
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(G, seed=42, k=0.5)

    # Node colors by type
    color_map = {
        "azure": "skyblue",
        "custom": "orange",
        "external": "lightgreen"
    }

    node_colors = [color_map.get(G.nodes[node].get(
        "type", "azure"), "gray") for node in G.nodes()]

    # Draw nodes, edges, and labels
    nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                           node_size=2000, edgecolors='black')
    nx.draw_networkx_edges(G, pos, arrowstyle='->',
                           arrowsize=20, edge_color='gray')
    nx.draw_networkx_labels(G, pos, labels={
                            n: G.nodes[n]["label"] for n in G.nodes()}, font_size=10, font_weight='bold')

    # Draw edge labels
    edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_color='darkred', font_size=9)

    plt.title("Azure Architecture Graph", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
