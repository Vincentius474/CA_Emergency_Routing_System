import sys
import math
import random
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.graph_utils import _safe_int, _safe_float

VEHICLE_PROFILES = {
    "ambulance": {
        "max_height": 3.0,
        "max_weight": 4.0,

        "min_lanes": 1,
        "avoid_closed": True,
        "traffic_multi": 1.0,
        "non_preferred_penalty": 3.0,

        "road_type": ["primary", "secondary", "tertiary", "unclassified", "primary_link", "service",
                    "residential", "busway", "secondary_link", "tertiary_link", "living_street"],

        "hard_constraints": ["max_height", "max_weight", "max_width"],
        "soft_constraints": ["min_lanes", "road_type", "avoid_closed"]
    },
    "fire_engine": {
        "max_height": 3.5,
        "max_weight": 12.0,

        "min_lanes": 2,
        "avoid_closed": True,
        "traffic_multi": 2.0,
        "non_preferred_penalty": 3.0,

        "road_type": ["primary", "secondary", "tertiary", "unclassified", "primary_link", "service",
                    "residential", "busway", "secondary_link", "tertiary_link", "living_street"],

        "hard_constraints": ["max_height", "max_weight", "max_width"],
        "soft_constraints": ["min_lanes", "road_type", "avoid_closed"]
    },
    "police_units": {
        "max_height": 2.5,
        "max_weight": 2.5,
        
        "min_lanes": 1,
        "avoid_closed": False,
        "traffic_multi": 2.0,
        "non_preferred_penalty": 3.0,
        
        "road_type": ["primary", "secondary", "tertiary", "unclassified", "primary_link", "service",
                    "residential", "busway", "secondary_link", "tertiary_link", "living_street"],
        
        "hard_constraints": ["max_height", "max_weight"],
        "soft_constraints": ["min_lanes", "road_type", "avoid_closed"]
    }
}

def validate_single_edge(EG, enode: Tuple, constraints: Dict[str, Any]) -> Tuple[bool, float]:
    """Validate a single edge-node against constraints."""
    data = EG.nodes[enode]
    total_penalty = 0.0

    if data.get("bridge", "no") in ("yes", "true", "1"):
        if "max_height" in constraints:
            height = _safe_float(data.get("maxheight", 5.0))
            if height > constraints["max_height"]:
                return False, math.inf
        
        if "max_weight" in constraints:
            weight = _safe_float(data.get("maxweight", 30.0))
            if weight > constraints["max_weight"]:
                return False, math.inf
            
    if data.get("tunnel", "no") in ("yes", "true", "1"):
        if "max_height" in constraints:
            height = _safe_float(data.get("maxheight", 4.5))
            if height > constraints["max_height"]:
                return False, math.inf
        
    if "min_lanes" in constraints:
        lanes = _safe_int(data.get("lanes"), default=2)
        if lanes < constraints["min_lanes"]:
            return False, math.inf
        
    if constraints.get("avoid_closed") and data.get("closed", True):
        total_penalty += constraints.get("non_preferred_penalty", 10.0)
    
    if "avoid_closed" in constraints:
        if constraints["avoid_closed"]:
            if data.get("closed", True):
                total_penalty += constraints.get("non_preferred_penalty", 10.0)

    if "tunnel" in constraints:
        if data.get("tunnel") not in constraints["tunnel"]:
            total_penalty += constraints.get("non_preferred_penalty", 10.0)
        
    if "bridge" in constraints:
        if data.get("bridge") not in constraints["bridge"]:
            total_penalty += constraints.get("non_preferred_penalty", 10.0)

    if "road_type" in constraints:
        if data.get("highway") not in constraints["road_type"]:
            total_penalty += constraints.get("non_preferred_penalty", 10.0)

    return True, total_penalty

def validate_route(EG, route_enodes: List[Tuple], constraints: Dict[str, Any]) -> Tuple[bool, float]:
    """Validate an entire route against constraints."""
    total_penalty = 0.0

    if not route_enodes:
        return False, math.inf
    else:
        for en in route_enodes:
            valid, penalty = validate_single_edge(EG, en, constraints)
            if not valid:
                return False, math.inf
            total_penalty += penalty

    return True, total_penalty

def simulate_random_traffic(EG: nx.DiGraph, low: float = 0.8, high: float = 2.0, seed: Optional[int] = None) -> Dict[str, float]:
    """Simulate random traffic multipliers for all edges."""
    if seed is not None:
        random.seed(seed)

    traffic_data = {}
    for en in EG.nodes:
        mult = round(random.uniform(low, high), 2)
        edge_id = _edge_id_str(en)
        traffic_data[edge_id] = mult
    return traffic_data

def apply_traffic_to_graph(EG: nx.DiGraph, traffic_data: Dict[str, float]):
    """Apply traffic multipliers to EG in-place."""
    for en in EG.nodes:
        edge_id = _edge_id_str(en)
        if edge_id in traffic_data:
            EG.nodes[en]["traffic_mult"] = traffic_data[edge_id]

def _edge_id_str(enode) -> str:
    """Create a unique string id for an edge-node tuple."""
    u, v, k = enode
    return f"{u}-{v}-{k}"