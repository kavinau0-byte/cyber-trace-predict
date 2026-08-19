import sys
from pathlib import Path
sys.path.insert(0, "/home/kavin/cyber-trace-predict")

from ml.location_predictor import load_complaints, load_atms, compute_withdrawal_hotspots, predict_withdrawal_zones
from ml.graph_model import build_graph, score_chain

complaints = load_complaints()
atms = load_atms()
hotspots = compute_withdrawal_hotspots(complaints)
base_graph, _ = build_graph(complaints)
base_node_list = list(base_graph.nodes())

# Test on CMP00001
sc = complaints[0]
cid = sc['complaint_id']
vlat, vlon = sc['victim_lat'], sc['victim_lon']

orig_chain = sc['mule_chain']
fake_chain = ['NOISE-01', 'NOISE-02']

orig_scores = score_chain([cid] + orig_chain, base_graph=base_graph, base_node_list=base_node_list)
fake_scores = score_chain(['CMP999999'] + fake_chain, base_graph=base_graph, base_node_list=base_node_list)

res_orig = predict_withdrawal_zones(cid, vlat, vlon, orig_chain, top_k=5, atms=atms, hotspots=hotspots, base_graph=base_graph, base_node_list=base_node_list)
res_fake = predict_withdrawal_zones(cid, vlat, vlon, fake_chain, top_k=5, atms=atms, hotspots=hotspots, base_graph=base_graph, base_node_list=base_node_list)

print("=== TEST COMPLAINT:", cid, "===")
print("Victim Location:", (vlat, vlon))

print("\n--- 1. ORIGINAL HIGH-CONFIDENCE MULE CHAIN ---")
print("Chain:", orig_chain)
print("GNN Mule Probabilities:", orig_scores)
print("Ranked Predictions:")
for idx, r in enumerate(res_orig, 1):
    print(f"  Rank {idx}: [{r['atm_id']}] {r['name']:<30s} loc=({r['lat']:.4f}, {r['lon']:.4f})  conf={r['confidence']:.4f}")

print("\n--- 2. SWAPPED LOW-CONFIDENCE FAKE CHAIN ---")
print("Chain:", fake_chain)
print("GNN Mule Probabilities:", fake_scores)
print("Ranked Predictions:")
for idx, r in enumerate(res_fake, 1):
    print(f"  Rank {idx}: [{r['atm_id']}] {r['name']:<30s} loc=({r['lat']:.4f}, {r['lon']:.4f})  conf={r['confidence']:.4f}")
