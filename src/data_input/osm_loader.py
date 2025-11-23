import os
import sys
import random
import osmnx as ox
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.visualisation import visualize_graph

class OSMLoader:
    """This class is responsible for loading the map and exporting it."""

    def __init__(self, subset=True, load=False, display=False,
        data_dir="../data/", place_name="City of Johannesburg Metropolitan Municipality, Gauteng, South Africa"):
        self.subset = subset
        self.load = load
        self.display = display
        self.data_dir = data_dir
        self.place_name = place_name

    def _ensure_dir_exists(self, file_path):
        """Ensure the directory for the given file exists."""
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        return file_path

    def _load_full_city(self, display=False, data_dir="../data/"):
        """Loads the full road network graph for the specified area."""
        G = ox.graph_from_place(self.place_name, network_type="drive")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)

        p_name = self.place_name.replace(",", "")

        edges_csv = self._ensure_dir_exists(f"{data_dir}{p_name}_edges.csv")
        nodes_csv = self._ensure_dir_exists(f"{data_dir}{p_name}_nodes.csv")
        graphml_file = self._ensure_dir_exists(f"{data_dir}{p_name}.graphml")

        _, G = self._export_edges_to_csv(G, edges_csv)
        self._export_nodes_mapping(G, nodes_csv)
        ox.save_graphml(G, graphml_file)

        print(f"Graph downloaded and saved")
        print(f"Graph has {len(G.nodes)} nodes and {len(G.edges)} edges.")

        if display:
            visualize_graph(G, self.place_name)

        return G

    def _load_subset_area(self, display=False, dist=3500, data_dir="../data/"):
        """Loads a subset of the road network graph for the specified 
        area within a given distance."""
        hwy_speeds = {
            "motorway": 120,
            "trunk": 100,
            "primary": 80,
            "secondary": 60,
            "tertiary": 40,
            "residential": 30,
            "unclassified": 30,
        }

        G = ox.graph_from_address(self.place_name, dist=dist, network_type="drive")

        p_name = self.place_name.replace(",", "")

        if G is None:
            print("Failed to load graph from bounding box...")
            SystemExit(1)
        else:
            G = ox.add_edge_speeds(G, hwy_speeds=hwy_speeds)
            G = ox.add_edge_travel_times(G)

            edges_csv = self._ensure_dir_exists(f"{data_dir}{p_name}_subset_edges.csv") 
            nodes_csv = self._ensure_dir_exists(f"{data_dir}{p_name}_subset_nodes.csv")  
            graphml_file = self._ensure_dir_exists(f"{data_dir}{p_name}_subset.graphml") 

            _, G = self._export_edges_to_csv(G, edges_csv)
            self._export_nodes_mapping(G, nodes_csv)
            ox.save_graphml(G, graphml_file)

            print(f"Graph subset downloaded and saved")
            print(f"Graph has {len(G.nodes)} nodes and {len(G.edges)} edges.")

            if display:
                visualize_graph(G, self.place_name)

        return G

    def _load_graph_from_file(self, file_path):
        """Loads a road network graph from a GraphML file."""
        if not os.path.exists(file_path):
            print(f"[ERROR] File {file_path} does not exist.")
            return None

        G = ox.load_graphml(file_path)
        print(f"Graph loaded, with {len(G.nodes)} nodes and {len(G.edges)} edges.")
        if self.display:
            visualize_graph(G, "Unknown: Loaded From File")

        return G

    def _export_nodes_mapping(self, G, csv_path="../data/nodes.csv"):
        """Export nodes with full OSM attributes to CSV."""
        self._ensure_dir_exists(csv_path)
        nodes = []
        for node_id, data in G.nodes(data=True):
            node_info = {
                "node_id": node_id,
                "lat": data.get("y"),
                "lon": data.get("x"),
                "street_count": data.get("street_count"),
                "highway": data.get("highway", "none"),
            }
            nodes.append(node_info)

        df_nodes = pd.DataFrame(nodes)
        df_nodes.to_csv(csv_path, index=False)

        return {"df_nodes": df_nodes, "nodes": nodes}

    def _export_edges_to_csv( self, G, csv_path="../data/edges.csv", closed_prob=0.003, high_traffic_prob=0.009):
        """Export edges with selected OSM attributes and coordinates to CSV."""
        self._ensure_dir_exists(csv_path)

        edges = []
        for u, v, k, data in G.edges(keys=True, data=True):
            u_lat = G.nodes[u]["y"]
            u_lon = G.nodes[u]["x"]
            v_lat = G.nodes[v]["y"]
            v_lon = G.nodes[v]["x"]

            closed = random.random() < closed_prob
            if closed:
                traffic_mult = 0.01
            else:
                traffic_mult = 1.0
                if random.random() < high_traffic_prob:
                    traffic_mult = random.uniform(2.0, 5.0)

            data["closed"] = closed
            data["traffic_mult"] = traffic_mult

            G[u][v][k]["closed"] = closed
            G[u][v][k]["traffic_mult"] = traffic_mult

            is_bridge = str(data.get("bridge", "no")).lower() in ("yes", "true", "1")
            is_tunnel = str(data.get("tunnel", "no")).lower() in ("yes", "true", "1")

            max_height = None
            max_weight = None

            if is_bridge:
                max_height = data.get("maxheight", 5.0)
                max_weight = data.get("maxweight", 30.0)
            elif is_tunnel:
                max_height = data.get("maxheight", 4.5)
                max_weight = None

            edge_info = {
                "edge_id": f"{u}_{v}_{k}",
                "u": u,
                "v": v,
                "key": k,
                "u_lat": u_lat,
                "u_lon": u_lon,
                "v_lat": v_lat,
                "v_lon": v_lon,
                "length_m": data.get("length"),
                "max_speed_kph": data.get("speed_kph", 80.0),
                "travel_time_s": data.get("travel_time"),
                "name": data.get("name", "unamed"),
                "highway": data.get("highway"),
                "oneway": data.get("oneway"),
                "lanes": data.get("lanes", "1"),
                "ref": data.get("ref", "unclassified"),
                "bridge": data.get("bridge", "no"),
                "tunnel": data.get("tunnel", "no"),
                "access": data.get("access", "yes"),
                "closed": data.get("closed", closed),
                "traffic_mult": data.get("traffic_mult", traffic_mult),
                "max_height_m": max_height,
                "max_weight_tons": max_weight,
            }

            edges.append(edge_info)

        df_edges = pd.DataFrame(edges)
        df_edges.to_csv(csv_path, index=False)

        return df_edges, G

    def osm_loader_main(self):
        """Main function to load the OSM graph either from file or by downloading."""
        if self.load:
            print("\n[INFO] Loading graph from file...")
            G = self._load_graph_from_file(
                os.path.join(
                    self.data_dir,
                    f"{self.place_name.replace(',', '')}.graphml"
                )
            )
            if G is None:
                print("[ERROR] Failed to load graph from file, falling back to download.")
                self.load = False
        else:
            if self.subset:
                print("\n[INFO] Loading sub-area for faster testing...")
                G = self._load_subset_area(display=self.display, data_dir=self.data_dir)
            else:
                print("\n[INFO] Loading full city...This may take a while...")
                G = self._load_full_city(display=self.display, data_dir=self.data_dir)

        return G

if __name__ == "__main__":

    data_dir = "../../data/"
    file_path = os.path.join(
        data_dir,
        "City of Cape Town Western Cape South Africa_subset.graphml"
    )

    OSM_Loader = OSMLoader(
        subset=True,
        load=False,
        display=True,
        data_dir=data_dir,
        place_name="City of Cape Town Western Cape South Africa"
    )
    OSM_Loader.osm_loader_main()
