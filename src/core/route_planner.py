import csv
import os
import sys
import random
import networkx as nx
from pathlib import Path
from copy import deepcopy
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.search_algorithms import astar_route, dijkstra_route, bidirectional_astar_route
from src.utils.graph_utils import load_edge_graph, compute_route_tt
from src.core.constraints import VEHICLE_PROFILES, validate_route

def _create_logs(route: dict, EG):
    """Create logs for the planned route."""
    street_names = []
    if not route or not route.get("route_nodes"):
        print("[WARN] No valid route found.")
        return
    else:
        ROUTE_LOG_PATH = "../data/route_logs/route_directions_log.csv"
        HEADER = ["step", "direction"]
        step = 1
        previous_road = None
        
        os.makedirs(os.path.dirname(ROUTE_LOG_PATH), exist_ok=True)
        file_exists = os.path.exists(ROUTE_LOG_PATH)
        with open(ROUTE_LOG_PATH, "a" if file_exists else "w", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(HEADER)
            
            for en in route["route_enodes"]:
                data = EG.nodes[en]
                road_name = data.get("name", "Unnamed road")
                highway = data.get("highway", "?")
                length = float(data.get("length", 0.0))
                speed = float(data.get("speed_kph", 0.0))
                
                action = "Continue on" if previous_road == road_name else "Take"
                description = (
                    f"{action} {road_name} "
                    f"[{highway} | {length:.0f} m | speed limit {speed:.0f} km/h]"
                )
                
                row = [step, description]
                writer.writerow(row)
                previous_road = road_name
                step += 1

                street_names.append(road_name)
            
            row = ["--", "--"]
            writer.writerow(row)

        return street_names

def relax_constraints(base: Dict[str, Any], level: int) -> Dict[str, Any]:
    """
    Produce a relaxed copy of constraints in stages.
    Level 0: original (no change)
    Level 1: remove 'road_type', 'traffic_multi'
    Level 2: remove 'min_lanes', keep avoid_closed=True
    Level 3: keep only avoid_closed (allow anything else)
    """
    c = deepcopy(base)

    if level == 0:
        return c
    if level >= 1:
        c.pop("road_type", None)
        c.pop("traffic_multi", None)
    if level >= 2:
        c.pop("min_lanes", None)
    if level >= 3:
        keep_keys = {"avoid_closed"}
        c = {k: v for k, v in c.items() if k in keep_keys}

    return c


def _run_search(EG: nx.DiGraph, start_node: int, target_node: int, allow_closed=False) -> Dict[str, Any]:
    """Call the requested shortest-path algorithm on the edge-based graph."""
    routes_found = {}

    route_djkstra = dijkstra_route(EG, start_node, target_node, allow_closed=allow_closed)
    route_astar = astar_route(EG, start_node, target_node, allow_closed=allow_closed)
    route_bidirectional = bidirectional_astar_route(EG, start_node, target_node, allow_closed=allow_closed)

    routes_found["dijkstra"] = route_djkstra
    routes_found["astar"] = route_astar
    routes_found["bidirectional_astar"] = route_bidirectional

    best_route = None
    best_time = float("inf")
    for key, route in routes_found.items():
        total_time = compute_route_tt(EG, route.get("route_enodes", []))
        if total_time < best_time:
            best_time = total_time
            best_route = route
    
    return best_route

def _plan_route(EG: nx.DiGraph, start_node: int, target_node: int, vehicle_type: str = "ambulance",
    max_relax_level: int = 3) -> Dict[str, Any]:
    """Plan a route with progressive constraint relaxation if needed."""

    _closed = VEHICLE_PROFILES[vehicle_type]["avoid_closed"]
    if vehicle_type not in VEHICLE_PROFILES:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")

    for level in range(0, max_relax_level + 1):
        constraints = relax_constraints(VEHICLE_PROFILES[vehicle_type], level)
        EG_work = EG.copy()
        print(f"[INFO] Trying vehicle='{vehicle_type}', relax_level={level} ...")
        res = _run_search(EG_work, start_node, target_node, allow_closed=_closed)

        if not res.get("route_enodes"):
            print("[WARN] No path found at this level.")

        valid, penalty = validate_route(
            EG_work,
            res["route_enodes"],
            constraints
        )

        res["valid"] = valid
        res["relax_level"] = level
        res["penalty"] = penalty
        res["start_node"] = start_node
        res["target_node"] = target_node
        res["vehicle_type"] = vehicle_type
        res["constraints_used"] = constraints
        res["expanded_nodes"] = res.pop("expanded", 0)
        res["total_time"] = compute_route_tt(EG_work, res["route_enodes"])

        if valid:
            print(f"[INFO] Success.. Relax level={level}, Total time={res['total_time']:.1f}s, Penalty={penalty:.1f}s")
            return {
                "start_node": res["start_node"],
                "target_node": res["target_node"],
                "route_nodes": res["route_nodes"],
                "route_enodes": res["route_enodes"],
                "cost": res["penalty"],
                "expanded_nodes": res["expanded_nodes"],
                "valid": res["valid"],
                "penalty": res["penalty"],
                "total_time": res["total_time"],
                "vehicle_type": res["vehicle_type"],
                "relax_level": res["relax_level"],
                "constraints_used": res["constraints_used"],
            }
        print("[WARN] Path found but invalid under constraints at this level.")
  
    return {
        "start_node": start_node,
        "target_node": target_node,
        "route_nodes": None,
        "route_enodes": None,
        "cost": float("inf"),
        "expanded_nodes": 0,
        "valid": False,
        "penalty": float("inf"),
        "total_time": float("inf"),
        "vehicle_type": vehicle_type,
        "relax_level": None,
        "constraints_used": None,
    }

def _plot_route_eg(EG: nx.DiGraph, route_enodes: List[int], show=True):
    """Plots the route on the edge graph."""
    fig, ax = plt.subplots(figsize=(10, 10))
    for enode, data in EG.nodes(data=True):
        ux = data["u_x"]
        uy = data["u_y"]
        vx = data["v_x"]
        vy = data["v_y"]
        ax.plot([ux, vx], [uy, vy], color='#cccccc', linewidth=0.3, alpha=0.5)

    if route_enodes:
        xs, ys = [], []
        for i in range(len(route_enodes) - 1):
            a = route_enodes[i]
            b = route_enodes[i + 1]
            match = None
            for enode, data in EG.nodes(data=True):
                if data.get("orig_u") == a and data.get("orig_v") == b:
                    match = (enode, data)
            if match is None:
                continue
            enode, data = match
            if not xs and not ys:
                xs.append(data["u_x"])
                ys.append(data["u_y"])
            xs.append(data["v_x"])
            ys.append(data["v_y"])
        
        if xs and ys:
            ax.plot(xs, ys, color="#ff3333", linewidth=2, label='Route')
    
    ax.set_title("Route on Edge Graph")
    ax.axis("equal")
    if show:
        plt.show()

def construct_route(EG: nx.DiGraph, start_node: Optional[int] = None, target_node: Optional[int] = None,
        vehicle_type: str = "fire_engine", max_relax_level: int = 3) -> Dict[str, Any]:
    """Main function to compute the route on the edge graph."""
    
    if start_node is None or target_node is None:
        orig_nodes = {data["orig_u"] for _, data in EG.nodes(data=True)} | {data["orig_v"] for _, data in EG.nodes(data=True)}
        if len(orig_nodes) < 2:
            raise ValueError("Graph does not have enough distinct original nodes to pick start/target.")
        start_node, target_node = random.sample(list(orig_nodes), 2)
        print(f"[INFO] Randomly selected start={start_node}, target={target_node}")

    print(f"\n[INFO] Planning route for {vehicle_type} from {start_node} to {target_node} ...")
    route = _plan_route(
        EG, start_node, target_node,
        vehicle_type=vehicle_type,
        max_relax_level=max_relax_level
    )

    street_names = []

    if route.get("route_nodes"):
        street_names = _create_logs(route, EG)
        print("Result:", {
            "total time (s)": route["total_time"],
            "expanded nodes": route["expanded_nodes"],
            "route_nodes": len(route["route_nodes"]) if route["route_nodes"] else 0,
            "penalty (s)": route["penalty"]
        })

    else:
        print("[ERROR] No valid route could be found with any relaxation level.")

    return {
        "expanded_nodes": route["expanded_nodes"],
        "route_enodes": route["route_enodes"],
        "route_nodes": route["route_nodes"],
        "total_time": route["total_time"],
        "street_names": street_names,
        "penalty": route["penalty"],
        "valid": route["valid"],
        "result": route,
        "graph": EG
    }

if __name__ == "__main__":

    GRAPH_PATH = "../../data/City of Johannesburg Metropolitan Municipality Gauteng South Africa_subset_edgegraph.gpickle"
    EG = load_edge_graph(GRAPH_PATH)
    route = construct_route(EG, start_node=590065154, target_node=2476496575, vehicle_type="ambulance")
    if route.get("route_nodes"):
        _plot_route_eg(EG, route["route_nodes"])
    else:
        print("No valid route found.")