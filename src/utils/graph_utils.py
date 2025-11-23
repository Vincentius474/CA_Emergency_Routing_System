import os
import csv
import math
import pickle
import networkx as nx
from datetime import datetime
from typing import List, Tuple

"""
Helper functions
"""

def load_edge_graph(file_path: str) -> nx.DiGraph:
    """
    Load the edge graph from a pickle file.
    """
    with open(file_path, 'rb') as f:
        EG = pickle.load(f)
    return EG

def enode_travel_time(EG: nx.DiGraph, enode) -> float:
    """
    Calculates the travel time for a given enode.
    """
    data = EG.nodes[enode]
    base_time_travel = float(data.get("travel_time", 0.0))
    mult = float(data.get("traffic_mult", 1.0))
    penalty = float(data.get("penalty", 0.0))
    return base_time_travel * mult + penalty

def is_enode_closed(EG: nx.DiGraph, enode) -> bool:
    """
    Checks if a given enode is closed.
    """
    return bool(EG.nodes[enode].get("closed", False))

def enodes_from_start(EG: nx.DiGraph, start_node_id) -> List[Tuple]:
    """
    Finds EG nodes that originate from start_node_id.
    """
    return [n for n, d in EG.nodes(data=True) if d.get("orig_u") == start_node_id]

def target_nodes(EG: nx.DiGraph, target_node_id) -> set:
    """
    Finds EG nodes that are targets for the given target_node_id.
    """
    return {n for n, d in EG.nodes(data=True) if d.get("orig_v") == target_node_id}

def compute_route_tt(EG: nx.DiGraph, route_enodes: List[Tuple]) -> float:
    """
    Computes the total travel time for a given route of enodes.
    """

    if not route_enodes:
        return math.inf
    
    total = 0.0
    total += enode_travel_time(EG, route_enodes[0])
    for i in range(1, len(route_enodes)):
        prev_enode = route_enodes[i - 1]
        curr_enode = route_enodes[i]

        turn_cost = 0.0
        if EG.has_edge(prev_enode, curr_enode):
            turn_cost = float(EG.edges[prev_enode, curr_enode].get("turn_cost", 0.0))

        # turn = float(EG[prev_enode][curr_enode].get("turn_penalty", 0.0))
        # total += turn 
        # total += enode_travel_time(EG, curr_enode)

        total += turn_cost
        total += enode_travel_time(EG, curr_enode)

    return total

def _is_number(val: str) -> bool:
    """
    Check if a value can be converted to a float.
    """
    try:
        float(val)
        return True
    except Exception:
        return False

def _safe_int(value, default=1) -> int:
    """
    Convert OSM attribute to int safely.
    """
    if value is None:
        return default
    if isinstance(value, list):
        try:
            return max(int(v) for v in value if str(v).isdigit())
        except ValueError:
            return default
    if isinstance(value, str):
        return int(value) if value.isdigit() else default
    try:
        return int(value)
    except Exception:
        return default
    
def _safe_float(value, default=1.0) -> float:
    """
    Convert OSM attribute to float safely.
    """
    if value is None:
        return default
    if isinstance(value, list):
        try:
            return max(float(v) for v in value if _is_number(v))
        except ValueError:
            return default
    if isinstance(value, str):
        return float(value) if _is_number(value) else default
    try:
        return float(value)
    except Exception:
        return default


