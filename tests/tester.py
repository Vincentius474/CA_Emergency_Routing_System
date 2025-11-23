import os
import sys
import time
import random
import pickle
import tracemalloc
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).parent.parent))
from src.data_input.osm_loader import OSMLoader
from src.data_input.graph_constructor import GraphConstructor
from src.core.route_planner import construct_route
from src.core.search_algorithms import dijkstra_route, astar_route, bidirectional_astar_route

def run_with_memory(func, *args, **kwargs):
    """
    Run a function with tracemalloc to capture runtime and memory usage.
    Returns (result, runtime, memory_dict).
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    t1 = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        'result': result,
        'run_time': (t1 - t0),
        'current_mb': current / 1e6,
        'peak_mb': peak / 1e6
    }

def test_map_loading():
    """Test graph size impact"""
    data_dir = "../data/"
    OSM_Loader = OSMLoader(subset=True, load=False, display=False, data_dir=data_dir, place_name="City of Johannesburg Metropolitan Municipality, Gauteng, South Africa")

    results = run_with_memory(OSM_Loader.osm_loader_main)
    print(f'\n Runtime : {(results["run_time"]):.3f} -> Current MB : {(results["current_mb"]):.3f} -> Peak MB : {(results["peak_mb"]):.3f} ->')

def test_algorithm(EG):
    """Test efficiency of each algorithm"""
    results = []
    list_nodes = list(EG.nodes)
    random_start = random.choice(list_nodes)[0]
    random_target = random.choice(list_nodes)[0]
    
    while random_start == random_target:
        random_start = random.choice(list_nodes)[0]
        random_target = random.choice(list_nodes)[0]

    outcomes = run_with_memory(construct_route, EG, random_start, random_target, "fire_engine")
    results.append("| astar results |")
    for key, value in outcomes.items():
        if key != 'result':
            results.append(f"{key} | {value}")

    outcomes = run_with_memory(construct_route, EG, random_start, random_target, "fire_engine")
    results.append("| bidirectional_astar results |")
    for key, value in outcomes.items():
        if key != 'result':
            results.append(f"{key} | {value}")

    outcomes = run_with_memory(construct_route, EG, random_start, random_target, "fire_engine")
    results.append("| dijkstra results |")
    for key, value in outcomes.items():
        if key != 'result':
            results.append(f"{key} | {value}")

    print(f'\n{results}')

def test_constraint_handling(EG):
    """Test constraints adherence"""
    results = []
    list_nodes = list(EG.nodes)
    random_start = random.choice(list_nodes)[0]
    random_target = random.choice(list_nodes)[0]
    
    while random_start == random_target:
        random_start = random.choice(list_nodes)[0]
        random_target = random.choice(list_nodes)[0]

    for i in range(4):
        outcomes = run_with_memory(construct_route, EG, random_start, random_target, "ambulance", i)
        results.append(f"| astar results : constraint level = {i}|")
        for key, value in outcomes.items():
            if key != 'result':
                results.append(f"{key} | {value}")
    
    print(f'\n{results}')

def test_nodes_over_time(EG):
    start = 319039819
    targets = [26417337, 54994392, 252020768, 252020772, 257925943, 300357077, 6930021781, 7169672270, 7169672270, 7169839389]
    targets.sort()

    astar_route_time = []
    astar_route_nodes = []
    dijkstra_route_time = []
    dijkstra_route_nodes = []
    bidirectional_route_time = []
    bidirectional_route_nodes = []
    
    for target in targets:
        astar_outcomes = run_with_memory(construct_route, EG, start, target, "fire_engine")
        astar_route_time.append(astar_outcomes['run_time'])
        results = astar_outcomes['result']
        astar_route_nodes.append(len(results['route_nodes']))

        dijkstra_outcomes = run_with_memory(construct_route, EG, start, target, "fire_engine")
        dijkstra_route_time.append(dijkstra_outcomes['run_time'])
        results = dijkstra_outcomes['result']
        dijkstra_route_nodes.append(len(results['route_nodes']))

        bidirectional_outcomes = run_with_memory(construct_route, EG, start, target, "fire_engine")
        bidirectional_route_time.append(bidirectional_outcomes['run_time'])
        results = bidirectional_outcomes['result']
        bidirectional_route_nodes.append(len(results['route_nodes']))

    _make_plot(astar_route_nodes, dijkstra_route_nodes, bidirectional_route_nodes,
               astar_route_time, dijkstra_route_time, bidirectional_route_time,
               ['astar', 'dijkstra', 'bidirectional A*'])

def _make_plot(x1_data, x2_data, x3_data, y1_data, y2_data, y3_data, labels):
    """For plotting results """

    colors = ['blue', 'green', 'orange']
    max_x = max(max(x1_data, x2_data, x3_data))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(x1_data, y1_data, color=colors[0], label=labels[0], linewidth=2)
    ax.scatter(x2_data, y2_data, color=colors[1], label=labels[1], linewidth=2)
    ax.scatter(x3_data, y3_data, color=colors[2], label=labels[2], linewidth=2)
 
    ax.set_title('# of Route Nodes vs Time Taken (s)')
    ax.set_xlabel('# of Route Nodes')
    ax.set_ylabel('Time Taken (s)')
    ax.set_xticks(np.arange(0, max_x, 10))
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
   
    # test_map_loading()

    data_dir = "../data/"
    G_Constructor = GraphConstructor(data_dir = data_dir, subset=True, label="City of Johannesburg Metropolitan Municipality Gauteng South Africa")
    G_Constructor.graph_constructor()

    with open("../data/City of Johannesburg Metropolitan Municipality Gauteng South Africa_subset_edgegraph.gpickle", "rb") as f:
        EG = pickle.load(f)

    # test_algorithm(EG)
    # test_constraint_handling(EG)

    test_nodes_over_time(EG)


