import os
import math
import pickle
import osmnx as ox
import numpy as np
import networkx as nx

class GraphConstructor:
    """This class is responsible for constructing an edge based graph."""
    def __init__(self, data_dir = "../data/", subset=True, label="City of Johannesburg Metropolitan Municipality Gauteng South Africa"):
        self.data_dir = data_dir
        self.subset = subset
        self.label = label

    def _project_graph_safe(self, G):
        """
        Safely projects a graph into a consistent coordinate system 
        for accurate spatial calculations.
        """
        try:
            return ox.project_graph(G)
        except:
            return ox.projection.project_graph(G)
        
    def _prepare_graph(self, G):
        """
        Enhances a raw OSMnx graph with:
        - project coordinates
        - edge speeds and travel time
        - default traffic multipliers and penalities
        """
        GP = self._project_graph_safe(G)
        try:
            GP = ox.add_edge_speeds(GP)
        except Exception as e:
            print(f'[WARNING] Could not add edge speeds: {e}')

        try:
            GP = ox.add_edge_travel_times(GP)
        except Exception as e:
            print(f'[WARNING] Could not add travel times: {e}')
            for u, v, k, data in GP.edges(keys = True, data = True):
                length = data.get("length", 1.0)
                speed_kph = data.get("speed_kph", 50)
                data["travel_time"] = float(length) / float((speed_kph) / 3.6)

        for u, v, k, data in GP.edges(keys = True, data = True):
            data.setdefault("traffic_mult", 1.0)
            data.setdefault("penalty", 0.0)
        
        return GP

    def _construct_edge_graph(self, GP, left_turn_mult=1.5, base_turn_penalty=1.0):
        """Converts a node-based graph into an edge-based graph."""
        EG = nx.DiGraph()
        for u, v, k, data in GP.edges(keys = True, data = True):
            enode = (u, v, k)
            EG.add_node(enode, **dict(data))
            EG.nodes[enode]["u_x"] = GP.nodes[u]["x"]
            EG.nodes[enode]["u_y"] = GP.nodes[u]["y"]
            EG.nodes[enode]["v_x"] = GP.nodes[v]["x"]
            EG.nodes[enode]["v_y"] = GP.nodes[v]["y"]
            EG.nodes[enode]["orig_u"] = u
            EG.nodes[enode]["orig_v"] = v
        
        for u, v, k in GP.edges(keys = True):
            from_enode = (u, v, k)
            for _, w, k2 in GP.out_edges(v, keys = True):
                to_enode = (v, w, k2)
                vec_in = np.array([
                    EG.nodes[from_enode]["v_x"] - EG.nodes[from_enode]["u_x"],
                    EG.nodes[from_enode]["v_y"] - EG.nodes[from_enode]["u_y"]
                ])
                vec_out = np.array([
                    EG.nodes[from_enode]["v_x"] - EG.nodes[to_enode]["u_x"],
                    EG.nodes[from_enode]["v_y"] - EG.nodes[to_enode]["u_y"]
                ])

                norm_in = np.linalg.norm(vec_in)
                norm_out = np.linalg.norm(vec_out)
                if (norm_in < 1e-9) or (norm_out < 1e-9):
                    angle_deg = 0.0
                else:
                    cos_angle = np.clip(np.dot(vec_in, vec_out) / (norm_in * norm_out), -1.0, 1.0)
                    angle_deg = math.degrees(math.acos(cos_angle))

                cross_z = vec_in[0] * vec_out[1] - vec_in[1] * vec_out[0]
                is_left = cross_z > 0
                angle_factor = angle_deg / 180.0
                multiplier = left_turn_mult if is_left else 1.0
                turn_cost = base_turn_penalty * (1.0 + 4.0 * angle_factor) * multiplier
                EG.add_edge(from_enode, to_enode, turn_cost=float(turn_cost))
        
        return EG

    def graph_constructor(self):
        """
        Orchestrates the entire pipeline
        - Loads an OSM graph.
        - Prepares the graph with speeds and travel times.
        - Constructs an edge-based graph with turn costs.
        - Saves the edge-based graph to a file.
        """
        label = f"{self.label}_subset" if self.subset else f"{self.label}"

        in_graphml = os.path.join(self.data_dir, f"{label}.graphml")
        out_node = f"{self.data_dir}{label}_prepared.graphml"
        out_edge = f"{self.data_dir}{label}_edgegraph.gpickle"

        if not os.path.exists(in_graphml):
            raise FileNotFoundError(f"Input graph file {in_graphml} does not exist.")
        print("\n[INFO] Loading GraphML...")
        G = ox.load_graphml(in_graphml)

        print("[INFO] Preparing node-based graph...")
        GP = self._prepare_graph(G)
        ox.save_graphml(GP, out_node)

        print("[INFO] Constructing edge-based graph with turn costs...")
        EG = self._construct_edge_graph(GP)
        with open(out_edge, "wb") as f:
            pickle.dump(EG, f)
        print(f"[INFO] Edge-based graph saved.")

if __name__ == "__main__":

    data_dir = "../../data/"
    G_Constructor = GraphConstructor(data_dir = data_dir, 
                                     subset=True, 
                                     label="City Gqeberha Nelson Mandela Bay Metropolitan Municipality Eastern Cape South Africa")
    G_Constructor.graph_constructor()
