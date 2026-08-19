"""
Task 4 -- GNN-based Mule Account Tracing
Builds a directed transaction graph from synthetic complaint data and trains a
2-layer Graph Convolutional Network (GCN) to classify whether a node is a
mule account. Includes an inference function to score hypothetical new chains.

Dependencies: torch, torch_geometric, networkx, scikit-learn
"""

import csv
import json
import random
from pathlib import Path

import networkx as nx
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

DATA_FILE = "data/synthetic_complaints.csv"
MODEL_FILE = "ml/mule_gnn.pt"

# Node type encoding (used for target labels, NOT input features)
NODE_TYPES = {"victim": 0, "mule": 1, "atm": 2, "noise": 3}
NUM_NODE_TYPES = len(NODE_TYPES)

# Training hyperparameters
HIDDEN_DIM = 64
EPOCHS = 200
LR = 0.01
WEIGHT_DECAY = 5e-4
TEST_SIZE = 0.2
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Data loading & graph construction
# ---------------------------------------------------------------------------

def load_complaints():
    """Load synthetic complaints CSV and return list of parsed dicts."""
    complaints = []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["mule_chain"] = json.loads(row["mule_chain"])
            if "noise_nodes" in row and row["noise_nodes"]:
                row["noise_nodes"] = json.loads(row["noise_nodes"])
            else:
                row["noise_nodes"] = []
            row["amount_inr"] = float(row["amount_inr"])
            complaints.append(row)
    return complaints


def build_graph(complaints):
    """Build a combined directed graph from all complaints.

    Each complaint contributes a chain:
        victim (CMPxxxxx) -> mule_chain[0] -> ... -> mule_chain[-1] -> withdrawal_atm_id
    Optional dead-end noise nodes receive transactions from mules/victims without forwarding.

    Returns:
        G: nx.DiGraph with node attributes 'node_type', 'hop_index', and 'total_amount'
        node_labels: dict mapping node_id -> int label (victim=0, mule=1, atm=2, noise=3)
    """
    G = nx.DiGraph()
    node_labels = {}

    for row in complaints:
        victim_id = row["complaint_id"]
        mule_chain = row["mule_chain"]
        atm_id = str(row["withdrawal_atm_id"])
        amount = float(row.get("amount_inr", 0.0))
        noise_nodes = row.get("noise_nodes", [])

        # Full chain: victim -> mules... -> ATM
        chain = [victim_id] + mule_chain + [atm_id]

        for idx, node_id in enumerate(chain):
            if idx == 0:
                ntype = "victim"
                hop = 0.0
            elif idx == len(chain) - 1:
                ntype = "atm"
                hop = float(idx)
            else:
                ntype = "mule"
                hop = float(idx)

            if node_id not in G:
                G.add_node(node_id, node_type=ntype, hop_index=hop, total_amount=amount, hop_sum=hop, hop_count=1)
                node_labels[node_id] = NODE_TYPES[ntype]
            else:
                # Reused node: update accumulated total_amount and average hop_index
                G.nodes[node_id]["total_amount"] = G.nodes[node_id].get("total_amount", 0.0) + amount
                curr_sum = G.nodes[node_id].get("hop_sum", G.nodes[node_id].get("hop_index", hop)) + hop
                curr_cnt = G.nodes[node_id].get("hop_count", 1) + 1
                G.nodes[node_id]["hop_sum"] = curr_sum
                G.nodes[node_id]["hop_count"] = curr_cnt
                G.nodes[node_id]["hop_index"] = curr_sum / curr_cnt

        # Add directed edges along the chain with transaction weight
        for i in range(len(chain) - 1):
            u, v = chain[i], chain[i + 1]
            if G.has_edge(u, v):
                G[u][v]["weight"] = G[u][v].get("weight", 0.0) + amount
            else:
                G.add_edge(u, v, weight=amount)

        # Process noise nodes (dead-end accounts receiving a transaction, not forwarding)
        for noise_id in noise_nodes:
            if noise_id not in G:
                G.add_node(noise_id, node_type="noise", hop_index=1.0, total_amount=amount, hop_sum=1.0, hop_count=1)
                node_labels[noise_id] = NODE_TYPES["noise"]
            else:
                G.nodes[noise_id]["total_amount"] = G.nodes[noise_id].get("total_amount", 0.0) + amount

            source_node = mule_chain[0] if mule_chain else victim_id
            if G.has_edge(source_node, noise_id):
                G[source_node][noise_id]["weight"] = G[source_node][noise_id].get("weight", 0.0) + amount
            else:
                G.add_edge(source_node, noise_id, weight=amount)

    return G, node_labels


def graph_to_pyg_data(G, node_labels):
    """Convert NetworkX graph to PyTorch Geometric Data object.

    Node feature vector (per node):
        [hop_index(1), in_degree(1), out_degree(1), total_amount_log(1), betweenness_centrality(1)] = 5 dims

    Note: One-hot encoding of node_type is explicitly EXCLUDED to prevent data leakage.
    """
    node_list = list(G.nodes())
    node_idx = {n: i for i, n in enumerate(node_list)}

    # Graph topological metrics
    bc = nx.betweenness_centrality(G)

    num_features = 5
    x = np.zeros((len(node_list), num_features), dtype=np.float32)
    y = np.zeros(len(node_list), dtype=np.int64)

    for i, node in enumerate(node_list):
        hop = float(G.nodes[node].get("hop_index", 0.0))
        in_deg = float(G.in_degree(node))
        out_deg = float(G.out_degree(node))
        amt = float(G.nodes[node].get("total_amount", 0.0))
        b_cent = float(bc.get(node, 0.0))

        x[i, 0] = hop
        x[i, 1] = in_deg
        x[i, 2] = out_deg
        x[i, 3] = np.log1p(amt)
        x[i, 4] = b_cent
        y[i] = node_labels[node]

    # Build edge index (COO format)
    edges = list(G.edges())
    if edges:
        src = [node_idx[e[0]] for e in edges]
        dst = [node_idx[e[1]] for e in edges]
        edge_index = torch.tensor([src, dst], dtype=torch.long)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    data = Data(
        x=torch.tensor(x, dtype=torch.float),
        edge_index=edge_index,
        y=torch.tensor(y, dtype=torch.long),
    )
    data.num_nodes = len(node_list)
    return data, node_list


# ---------------------------------------------------------------------------
# GCN model
# ---------------------------------------------------------------------------

class MuleGCN(torch.nn.Module):
    """2-layer GCN for node-level mule account classification."""

    def __init__(self, in_dim, hidden_dim, out_dim):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, out_dim)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        return x


# ---------------------------------------------------------------------------
# Training & evaluation
# ---------------------------------------------------------------------------

def train_model(data, node_list):
    """Train GCN and return trained model + test metrics."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Node-level train/test split
    indices = list(range(data.num_nodes))
    train_idx, test_idx = train_test_split(
        indices, test_size=TEST_SIZE, random_state=RANDOM_STATE,
        stratify=data.y.cpu().numpy(),
    )
    train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    train_mask[train_idx] = True
    test_mask[test_idx] = True

    data = data.to(device)
    model = MuleGCN(data.x.shape[1], HIDDEN_DIM, NUM_NODE_TYPES).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    criterion = torch.nn.CrossEntropyLoss()

    # Training loop
    model.train()
    for epoch in range(1, EPOCHS + 1):
        optimizer.zero_grad()
        out = model(data)
        loss = criterion(out[train_mask], data.y[train_mask])
        loss.backward()
        optimizer.step()

        if epoch % 50 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                preds = out[test_mask].argmax(dim=1)
                correct = (preds == data.y[test_mask]).sum().item()
                acc = correct / test_mask.sum().item()
            print(f"  Epoch {epoch:>3d}/{EPOCHS}  loss={loss.item():.4f}  test_acc={acc:.4f}")
            model.train()

    # Final evaluation
    model.eval()
    with torch.no_grad():
        out = model(data)
        test_preds = out[test_mask].argmax(dim=1).cpu().numpy()
        test_true = data.y[test_mask].cpu().numpy()

    # Map numeric labels back to names for the report
    rev_node_types = {v: k for k, v in NODE_TYPES.items()}
    present_classes = sorted(list(set(test_true) | set(test_preds)))
    target_names = [rev_node_types[i] for i in present_classes]
    print("\n=== Mule GCN -- Test Set Performance ===")
    print(classification_report(test_true, test_preds, target_names=target_names, labels=present_classes))

    # Save model + metadata
    torch.save({
        "model_state_dict": model.state_dict(),
        "in_dim": data.x.shape[1],
        "node_list": node_list,
    }, MODEL_FILE)
    print(f"Model saved -> {MODEL_FILE}")

    return model, data, node_list, device


def load_model():
    """Load trained model from disk."""
    checkpoint = torch.load(MODEL_FILE, weights_only=False)
    model = MuleGCN(checkpoint["in_dim"], HIDDEN_DIM, NUM_NODE_TYPES)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint["node_list"]


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def score_chain(chain_accounts, model=None, base_graph=None, base_node_list=None):
    """Score a hypothetical mule chain for mule-likelihood."""
    if model is None:
        model, base_node_list = load_model()
        base_graph, _ = build_graph(load_complaints())

    if base_graph is None:
        base_graph, _ = build_graph(load_complaints())
        base_node_list = list(base_graph.nodes())

    work_graph = base_graph.copy()
    chain = list(chain_accounts)

    for idx in range(len(chain) - 1):
        work_graph.add_edge(chain[idx], chain[idx + 1])

    for idx, node_id in enumerate(chain):
        if node_id not in base_graph:
            if node_id.startswith("NOISE"):
                ntype = "noise"
            elif idx == 0:
                ntype = "victim"
            elif idx == len(chain) - 1:
                ntype = "atm"
            else:
                ntype = "mule"
            work_graph.add_node(node_id, node_type=ntype, hop_index=float(idx), total_amount=0.0)

    all_labels = {n: NODE_TYPES.get(work_graph.nodes[n].get("node_type", "mule"), 1)
                  for n in work_graph.nodes()}
    data, all_nodes = graph_to_pyg_data(work_graph, all_labels)
    node_idx = {n: i for i, n in enumerate(all_nodes)}

    model.eval()
    with torch.no_grad():
        out = model(data)
        probs = F.softmax(out, dim=1)

    scores = []
    for node_id in chain:
        idx = node_idx[node_id]
        mule_prob = probs[idx, 1].item()
        scores.append(round(mule_prob, 4))

    return scores


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading complaints...")
    complaints = load_complaints()
    print(f"  {len(complaints)} complaints loaded")

    print("Building transaction graph...")
    G, node_labels = build_graph(complaints)
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    type_counts = {}
    rev_node_types = {v: k for k, v in NODE_TYPES.items()}
    for lbl in node_labels.values():
        name = rev_node_types[lbl]
        type_counts[name] = type_counts.get(name, 0) + 1
    print(f"  Node types: {type_counts}")

    data, node_list = graph_to_pyg_data(G, node_labels)

    print("\nTraining GCN...")
    model, data, node_list, device = train_model(data, node_list)

    # Demo: score one chain from the dataset
    print("\n=== Demo: score_chain() on a sample complaint ===")
    sample = complaints[0]
    demo_chain = [sample["complaint_id"]] + sample["mule_chain"] + [str(sample["withdrawal_atm_id"])]
    print(f"  Chain: {' -> '.join(demo_chain)}")
    print(f"  Actual mule labels: {[sample['complaint_id']]}(victim) + "
          f"{sample['mule_chain']}(mules) + [{sample['withdrawal_atm_id']}](atm)")

    scores = score_chain(demo_chain, model=model, base_graph=G, base_node_list=node_list)
    print(f"  Mule-likelihood scores: {scores}")

    for node_id, score in zip(demo_chain, scores):
        label = "MULE" if "MULE" in str(node_id) else ("VICTIM" if "CMP" in str(node_id) else ("NOISE" if "NOISE" in str(node_id) else "ATM"))
        print(f"    {node_id:>20s}  [{label:>6s}]  mule_prob={score:.4f}")


if __name__ == "__main__":
    main()
