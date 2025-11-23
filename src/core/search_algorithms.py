import math
import heapq
import networkx as nx
from typing import Dict, Any, List, Tuple, Optional

from src.core.constraints import validate_single_edge
from src.utils.graph_utils import enode_travel_time, enodes_from_start, is_enode_closed, target_nodes

def dijkstra_route(EG: nx.DiGraph, start_node_id, target_node_id, constraints=None,
                   allow_closed: bool = False, max_visits: Optional[int] = None) -> Dict[str, Any]:
    """
    Dijkstra's algorithm (edge-based).
    """

    start_enodes = enodes_from_start(EG, start_node_id)
    target_enodes = target_nodes(EG, target_node_id)

    if not start_enodes or not target_enodes:
        return {"route_nodes": None, "route_enodes": None, "cost": math.inf, "expanded": 0}

    if constraints:
        start_enodes = [en for en in start_enodes if validate_single_edge(EG, en, constraints)[0]]
        target_enodes = [en for en in target_enodes if validate_single_edge(EG, en, constraints)[0]]

    pq: List[Tuple[float, Tuple]] = []
    dist: Dict[Tuple, float] = {}
    prev: Dict[Tuple, Optional[Tuple]] = {}
    expanded: int = 0

    for enode in start_enodes:
        if not allow_closed and is_enode_closed(EG, enode):
            continue
        init_cost = enode_travel_time(EG, enode)
        dist[enode] = init_cost
        prev[enode] = None
        heapq.heappush(pq, (init_cost, enode))

    visited = set()
    best_target, best_cost = None, math.inf

    while pq:
        cost_u, enode = heapq.heappop(pq)
        if max_visits is not None and expanded >= max_visits:
            break
        if cost_u > dist.get(enode, math.inf):
            continue

        expanded += 1
        if enode in target_enodes:
            best_target, best_cost = enode, cost_u
            break

        visited.add(enode)
        for neighbor in EG.successors(enode):
            if not allow_closed and is_enode_closed(EG, neighbor):
                continue
            turn_cost = float(EG.edges[enode, neighbor].get("turn_cost", 0.0))
            travel_time = enode_travel_time(EG, neighbor)
            candidate = cost_u + turn_cost + travel_time

            if candidate < dist.get(neighbor, math.inf):
                dist[neighbor] = candidate
                prev[neighbor] = enode
                heapq.heappush(pq, (candidate, neighbor))

    if best_target is None:
        return {"route_nodes": None, "route_enodes": None, "cost": math.inf, "expanded": expanded}

    path_enodes = []
    current = best_target
    while current is not None:
        path_enodes.append(current)
        current = prev.get(current)
    path_enodes.reverse()

    route_nodes = []
    for idx, enode in enumerate(path_enodes):
        u, v, _k = enode
        if idx == 0:
            route_nodes.extend([u, v])
        else:
            route_nodes.append(v)

    return {"route_nodes": route_nodes, "route_enodes": path_enodes, "cost": best_cost, "expanded": expanded}

def astar_route(EG: nx.DiGraph, start_node_id, target_node_id, constraints=None,
                vmax_mps: float = 30.0, allow_closed: bool = False,
                max_visits: Optional[int] = None) -> Dict[str, Any]:
    """
    A* algorithm (edge-based).
    """

    start_enodes = enodes_from_start(EG, start_node_id)
    target_enodes = target_nodes(EG, target_node_id)

    if not start_enodes or not target_enodes:
        return {"route_nodes": None, "route_enodes": None, "cost": math.inf, "expanded": 0}

    if constraints:
        start_enodes = [en for en in start_enodes if validate_single_edge(EG, en, constraints)[0]]
        target_enodes = [en for en in target_enodes if validate_single_edge(EG, en, constraints)[0]]

    sample_target = next(iter(target_enodes))
    tx, ty = EG.nodes[sample_target]["v_x"], EG.nodes[sample_target]["v_y"]

    def heuristic(enode) -> float:
        vx, vy = EG.nodes[enode]["v_x"], EG.nodes[enode]["v_y"]
        d = math.hypot(vx - tx, vy - ty)
        return d / float(vmax_mps)

    open_heap: List[Tuple[float, float, Tuple]] = []
    gscore: Dict[Tuple, float] = {}
    prev: Dict[Tuple, Optional[Tuple]] = {}
    expanded: int = 0

    for enode in start_enodes:
        if not allow_closed and is_enode_closed(EG, enode):
            continue
        g = enode_travel_time(EG, enode)
        gscore[enode] = g
        prev[enode] = None
        heapq.heappush(open_heap, (g + heuristic(enode), g, enode))

    visited = set()
    best_target, best_cost = None, math.inf

    while open_heap:
        _, g, enode = heapq.heappop(open_heap)
        if max_visits is not None and expanded >= max_visits:
            break
        if enode in visited:
            continue
        visited.add(enode)

        if g > gscore.get(enode, math.inf):
            continue

        expanded += 1
        if enode in target_enodes:
            best_target, best_cost = enode, g
            break

        for neighbor in EG.successors(enode):
            if not allow_closed and is_enode_closed(EG, neighbor):
                continue
            turn_cost = float(EG.edges[enode, neighbor].get("turn_cost", 0.0))
            travel_time = enode_travel_time(EG, neighbor)
            tentative_g = g + turn_cost + travel_time

            if tentative_g < gscore.get(neighbor, math.inf):
                gscore[neighbor] = tentative_g
                prev[neighbor] = enode
                f = tentative_g + heuristic(neighbor)
                heapq.heappush(open_heap, (f, tentative_g, neighbor))

    if best_target is None:
        return {"route_nodes": None, "route_enodes": None, "cost": math.inf, "expanded": expanded}

    path_enodes = []
    current = best_target
    while current is not None:
        path_enodes.append(current)
        current = prev.get(current)
    path_enodes.reverse()

    route_nodes = []
    for idx, enode in enumerate(path_enodes):
        u, v, _k = enode
        if idx == 0:
            route_nodes.extend([u, v])
        else:
            route_nodes.append(v)

    return {"route_nodes": route_nodes, "route_enodes": path_enodes, "cost": best_cost, "expanded": expanded}

def bidirectional_astar_route(EG: nx.DiGraph, start_node_id, target_node_id,
                        vmax_mps: float = 30.0, allow_closed: bool = False,
                        constraints=None, max_visits: Optional[int] = None) -> Dict[str, Any]:
    """
    Bidirectional A* search on an edge-based graph.
    """

    start_enodes = enodes_from_start(EG, start_node_id)
    target_enodes = target_nodes(EG, target_node_id)

    if not start_enodes or not target_enodes:
        return {"route_nodes": None, "route_enodes": None, "cost": math.inf, "expanded": 0}

    if constraints:
        start_enodes = [en for en in start_enodes if validate_single_edge(EG, en, constraints)[0]]
        target_enodes = [en for en in target_enodes if validate_single_edge(EG, en, constraints)[0]]

    sample_target = next(iter(target_enodes))
    tx, ty = EG.nodes[sample_target]["v_x"], EG.nodes[sample_target]["v_y"]

    sample_start = next(iter(start_enodes))
    sx, sy = EG.nodes[sample_start]["u_x"], EG.nodes[sample_start]["u_y"]

    def heuristic_forward(enode):
        vx, vy = EG.nodes[enode]["v_x"], EG.nodes[enode]["v_y"]
        return math.hypot(vx - tx, vy - ty) / vmax_mps

    def heuristic_backward(enode):
        vx, vy = EG.nodes[enode]["u_x"], EG.nodes[enode]["u_y"]
        return math.hypot(vx - sx, vy - sy) / vmax_mps

    open_fwd, open_bwd = [], []
    g_fwd, g_bwd = {}, {}
    prev_fwd, prev_bwd = {}, {}

    expanded = 0

    for en in start_enodes:
        if not allow_closed and is_enode_closed(EG, en):
            continue
        g = enode_travel_time(EG, en)
        g_fwd[en] = g
        prev_fwd[en] = None
        heapq.heappush(open_fwd, (g + heuristic_forward(en), g, en))

    for en in target_enodes:
        if not allow_closed and is_enode_closed(EG, en):
            continue
        g = enode_travel_time(EG, en)
        g_bwd[en] = g
        prev_bwd[en] = None
        heapq.heappush(open_bwd, (g + heuristic_backward(en), g, en))

    best_cost = math.inf
    meeting_node = None

    while open_fwd and open_bwd:
        if max_visits and expanded >= max_visits:
            break

        if open_fwd:
            _, g, enode = heapq.heappop(open_fwd)
            expanded += 1
            if g > g_fwd.get(enode, math.inf):
                continue

            if enode in g_bwd:
                total_cost = g + g_bwd[enode]
                if total_cost < best_cost:
                    best_cost = total_cost
                    meeting_node = enode

            for neighbor in EG.successors(enode):
                if not allow_closed and is_enode_closed(EG, neighbor):
                    continue
                turn_cost = float(EG.edges[enode, neighbor].get("turn_cost", 0.0))
                travel_time = enode_travel_time(EG, neighbor)
                tentative_g = g + turn_cost + travel_time
                if tentative_g < g_fwd.get(neighbor, math.inf):
                    g_fwd[neighbor] = tentative_g
                    prev_fwd[neighbor] = enode
                    heapq.heappush(open_fwd, (tentative_g + heuristic_forward(neighbor), tentative_g, neighbor))

        if open_bwd:
            _, g, enode = heapq.heappop(open_bwd)
            expanded += 1
            if g > g_bwd.get(enode, math.inf):
                continue

            if enode in g_fwd:
                total_cost = g + g_fwd[enode]
                if total_cost < best_cost:
                    best_cost = total_cost
                    meeting_node = enode

            for neighbor in EG.predecessors(enode):
                if not allow_closed and is_enode_closed(EG, neighbor):
                    continue
                turn_cost = float(EG.edges[neighbor, enode].get("turn_cost", 0.0))
                travel_time = enode_travel_time(EG, neighbor)
                tentative_g = g + turn_cost + travel_time
                if tentative_g < g_bwd.get(neighbor, math.inf):
                    g_bwd[neighbor] = tentative_g
                    prev_bwd[neighbor] = enode
                    heapq.heappush(open_bwd, (tentative_g + heuristic_backward(neighbor), tentative_g, neighbor))

    if meeting_node is None:
        return {"route_nodes": None, "route_enodes": None, "cost": math.inf, "expanded": expanded}

    path_fwd, current = [], meeting_node
    while current is not None:
        path_fwd.append(current)
        current = prev_fwd.get(current)
    path_fwd.reverse()

    path_bwd, current = [], prev_bwd.get(meeting_node)
    while current is not None:
        path_bwd.append(current)
        current = prev_bwd.get(current)

    path_enodes = path_fwd + path_bwd
    route_nodes = []
    for idx, en in enumerate(path_enodes):
        u, v, _k = en
        if idx == 0:
            route_nodes.extend([u, v])
        else:
            route_nodes.append(v)

    return {"route_nodes": route_nodes, "route_enodes": path_enodes,
            "cost": best_cost, "expanded": expanded}