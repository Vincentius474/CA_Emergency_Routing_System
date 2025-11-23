import os
import csv
import sys
import random
import pickle
import threading
import matplotlib

matplotlib.use("TkAgg")
import tkinter as tk
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from tkinter import filedialog, messagebox, ttk

sys.path.append(str(Path(__file__).parent.parent.parent))
current_dir = Path(__file__).parent

from data_input.osm_loader import OSMLoader
from data_input.graph_constructor import GraphConstructor
from core.route_planner import construct_route
from core.constraints import apply_traffic_to_graph, simulate_random_traffic
from src.utils.visualisation import RouteVisualizer, convert_edge_route_to_node_route, RoutingLogTable

class UserInterface:
    """User Interface"""
    
    def __init__(self, root):
        """Initialize the user interface for the emergency routing system."""
        self.root = root
        self.root.title("Emergency Routing System - Control Panel")
        self.root.iconbitmap("./ui_icon.ico")
        self.root.geometry("1000x700")
        self.root.configure(bg="gray")

        self.target = None
        self.graph = None
        self.ori_graph = None
        self.step_count = 0
        self.visualizer = None
        self.current_node = None
        self.current_route = None
        self.movement_timer = None
        self.current_position_index = 0
        self.initial_planned = False
        self.street_names = []
        self.start_node = tk.StringVar()
        self.target_node = tk.StringVar()
        self.subset = tk.BooleanVar(value=True)
        self.vehicle_type = tk.StringVar(value="ambulance")
        self.place = tk.StringVar(value="City of Johannesburg Metropolitan Municipality Gauteng South Africa")

        self.replan_colors = list(mcolors.TABLEAU_COLORS.values())
        self.replan_colors.extend(["#3C103C", '#008080', '#00FFFF', '#800080', '#FFA500', '#A52A2A'])

        os.makedirs("../data/route_logs", exist_ok=True)
        self.log_file_path = "../data/route_logs/routing_log.csv"
        self._build_layout()

    def _build_layout(self):
        """Build the layout of the user interface with log table at row 5."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, sticky="nsew", rowspan=5)
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=5, column=0, sticky="nsew")
        
        for i in range(5):
            main_frame.grid_rowconfigure(i, weight=0)
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        self._build_control_panel(control_frame)
        self.display_table = RoutingLogTable(log_frame, self.log_file_path)
        self.display_table.pack(fill=tk.BOTH, expand=True, pady=0, padx=0)

    def _build_control_panel(self, parent):
        """Build the control panel."""
        style = ttk.Style()
        style.configure('Status.TLabel', 
                background='lightgray', 
                font=('Tahoma', 11),
                padding=(10, 5),
                anchor='center')

        frm = ttk.Frame(parent)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="City of Operation").grid(row=0, column=0, columnspan=3, sticky="w", padx=0, pady=15)
        ttk.Combobox(frm, textvariable=self.place, values=[
            "City of Johannesburg Metropolitan Municipality Gauteng South Africa",
            "City of Tshwane Metropolitan Municipality Gauteng South Africa",
            "City of Ekurhuleni Metropolitan Municipality Gauteng South Africa",
            "City of Polokwane Capricorn District Municipality Limpopo South Africa",
            "City of Durban eThekwini Metropolitan KwaZulu-Natal South Africa",
            "City of Cape Town Western Cape South Africa",
            ]).grid(row=0, column=0, columnspan=3, padx=25, pady=0)
        ttk.Label(frm, text="Vehicle Model").grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=25)
        ttk.Combobox(frm, textvariable=self.vehicle_type, values=["ambulance", "fire_engine", "police_units"]).grid(row=1, column=0, columnspan=3, padx=25, pady=0)

        ttk.Button(frm, text="Setup System", command=self.load_graph).grid(row=0, column=3, padx=15, pady=15)
        ttk.Button(frm, text="System Reset", command=self.reset_all).grid(row=0, column=4, padx=15, pady=15)
        ttk.Button(frm, text="Initiate Respond", command=self.set_start_target).grid(row=1, column=3, padx=15, pady=15)
        ttk.Button(frm, text="Manual Reroute", command=self.reroute_from_current).grid(row=1, column=4, padx=5, pady=10)
    
        self.status_label = ttk.Label(frm, text="Load map to begin.....", style='Status.TLabel')
        self.status_label.grid(row=4, column=0, columnspan=7, padx=0, pady=0, sticky='ew')

        for i in range(7):
            frm.grid_columnconfigure(i, weight=1)

    def add_event(self, logfile, start, target, total_time, penalty, route_length, reason):
        """Append an event to a CSV log file."""
        header = ["timestamp", "start", "target", "total_time", "penalty", "route_length", "reason"]
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [ts, start, target, f"{total_time:.2f}", f"{penalty:.2f}", route_length, reason]

        try:
            os.makedirs(os.path.dirname(logfile), exist_ok=True)
            file_exists = os.path.exists(logfile)
            with open(logfile, "a" if file_exists else "w", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(header)
                writer.writerow(row)
        except Exception as e:
            print(f"Warning: Could not write to log file {logfile}: {e}")

    def _log_event(self, start, target, total_time, penalty, route_length, reason):
        """Log an event and update the table."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [
            timestamp, str(start), str(target), f"{float(total_time):.2f}", 
            f"{float(penalty):.2f}", int(route_length), str(reason)
        ]
        self.add_event(self.log_file_path, start, target, total_time, penalty, route_length, reason)
        if hasattr(self, 'display_table'):
            self.root.after(0, lambda: self.display_table.add_log_entry(log_entry))

    def load_graph(self):
        """Load a graph from a file and initialize the visualizer."""
        try:
            self.status_label.config(text="Loading map data...")
            self.root.update()

            OSM_Loader = OSMLoader(subset=True, display=False, data_dir="../data/", place_name=self.place.get())
            self.ori_graph = OSM_Loader.osm_loader_main()
            
            G_Constructor = GraphConstructor(data_dir="../data/", subset=True, label=self.place.get())
            G_Constructor.graph_constructor()
            gpickle_path = f"{self.place.get()}_subset_edgegraph.gpickle" if self.subset.get() else f"{self.place.get()}_edgegraph.gpickle"
            file_path = os.path.join(current_dir, "../data/", gpickle_path)
            
            if not os.path.exists(file_path):
                messagebox.showerror("File Not Found", f"Graph file not found at: {file_path}")
                return  
            with open(file_path, "rb") as f:
                self.graph = pickle.load(f)

            self.initial_planned = False
            self.step_count = 0
            self.current_route = None
            self.current_node = None
 
            if self.visualizer is not None:
                self.visualizer.close_map()
            
            self.visualizer = RouteVisualizer(self.graph, self.ori_graph, self.place.get())
            self.status_label.config(text=f"Map loaded with {len(self.graph.nodes)} nodes.")
            self.display_map()
            messagebox.showinfo("Map Loaded", f"Loaded map with {len(self.graph.nodes)} nodes.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load graph: {str(e)}")
            self.status_label.config(text="Error loading map")

    def display_map(self):
        """Show the map in a separate window."""
        if self.visualizer is None:
            messagebox.showwarning("No map", "Please load a mao first.")
            return
        try:
            self.visualizer.display_map()
            self.status_label.config(text="Map displayed in separate window")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show map: {str(e)}")

    def clear_routes(self):
        """Clear all routes from the map and stop any ongoing movement."""
        if self.visualizer is None:
            messagebox.showwarning("No Graph", "Please load a graph first.")
            return

        self.stop_movement()
        if self.visualizer:
            self.visualizer.clear_vehicle_position()

        self.visualizer.clear_routes()
        self.current_route = None
        self.initial_planned = False
        self.step_count = 0
        self.current_position_index = 0
        self.status_label.config(text="All routes cleared and movement stopped")

    def reset_all(self):
        """Reset everything including the map and movement state."""
        self.stop_movement()
        
        if self.visualizer is not None:
            self.visualizer.clear_vehicle_position()
            self.visualizer.close_map()
        self.visualizer = None
        self.graph = None
        self.ori_graph = None
        self.initial_planned = False
        self.step_count = 0
        self.current_route = None
        self.current_node = None
        self.current_position_index = 0
        self.start_node.set("")
        self.target_node.set("")
        self.status_label.config(text="Load map to begin.....")

    def set_start_target(self):
        """Set the start and target nodes."""
        if not self.graph:
            messagebox.showwarning("No map loaded", "Please load map first.")
            return
        
        en_start = random.choice(list(self.graph.nodes))
        self.start_node.set(int(self.graph.nodes[en_start].get("orig_u", en_start)))

        en_target = random.choice(list(self.graph.nodes))
        while en_target == en_start:
            en_target = random.choice(list(self.graph.nodes))
        self.target_node.set(int(self.graph.nodes[en_target].get("orig_v", en_target)))

        self.run_initial()


    def start_movement_after_planning(self):
        """Starts movement simulation after route planning is complete."""
        if self.current_route and self.visualizer:
            self.visualizer.clear_vehicle_position()
            node_route = convert_edge_route_to_node_route(self.graph, self.current_route["route_enodes"])
            self.visualizer.plot_route(node_route, color="#E6131382", label="Initial Route")
            start_node = self.current_route["route_nodes"][0]
            self.visualizer.update_vehicle_position(start_node)
            self.root.after(1000, self.start_movement)

    def start_movement(self):
        """Starts or resumes vehicle movement along the route."""
        if not self.current_route or not self.visualizer:
            messagebox.showwarning("No Route", "Please plan a route first using 'Run Initial Router'.")
            return
        
        if self.movement_timer is None and self.current_position_index > 0:
            self.simulate_movement()
            return
        
        if self.current_position_index == 0:
            self.visualizer.update_vehicle_position(self.current_route["route_nodes"][0])
        
        self.simulate_movement()

    def pause_movement(self):
        """Pause the vehicle movement."""
        self.stop_movement()
        self.status_label.config(text="Movement paused")

    def resume_movement(self):
        """Resume paused vehicle movement."""
        if self.current_route and self.current_position_index < len(self.current_route["route_nodes"]):
            self.start_movement()
        else:
            messagebox.showinfo("Info", "No movement to resume or journey completed.")

    def stop_movement(self):
        """Stop the vehicle movement simulation."""
        if self.movement_timer:
            self.root.after_cancel(self.movement_timer)
            self.movement_timer = None


    def simulate_movement(self):
        """Simulate vehicle movement along the route step by step."""
        if not self.current_route:
            return
        
        route_nodes = self.current_route["route_nodes"]
        if self.current_position_index >= len(route_nodes):
            final_street = self.street_names[-1] if self.street_names else "Destination"
            self.status_label.config(text=f"Destination Reached - {final_street}")
            self.visualizer.update_vehicle_position(route_nodes[-1], color="#00FF00")
            return
        
        current_node = route_nodes[self.current_position_index]
        self.current_node = current_node
        
        current_street = "Unknown Street"
        next_street = self.street_names[-1] if self.street_names else "Next Location"
        if self.street_names and self.current_position_index < len(self.street_names):
            current_street = self.street_names[self.current_position_index]
            
        if self.street_names and (self.current_position_index + 1) < len(self.street_names):
            next_street = self.street_names[self.current_position_index + 1]
        elif self.current_position_index + 1 >= len(route_nodes):
            next_street = "Destination"
        
        vehicle_color = "#FFA500" if self.current_position_index == 0 else "#158913"
        if self.current_position_index == len(route_nodes) - 1:
            vehicle_color = "#00FF00"
        
        self.visualizer.update_vehicle_position(current_node, color=vehicle_color)
        self.status_label.config(text=f"Current Location: {current_street} | Approaching -> {next_street}")

        self.current_position_index += 1
        if self.current_position_index < len(route_nodes):
            delay = max(500, 2000 // len(route_nodes))
            self.movement_timer = self.root.after(delay, self.simulate_movement)
        else:
            final_street = self.street_names[-1] if self.street_names else "Destination"
            self.status_label.config(text=f"Destination Reached - {final_street}")

    def reroute_from_current(self):
        """Reroute from the vehicle's current position to the target."""
        if self.current_node is None:
            messagebox.showwarning("No Position", "Vehicle not positioned yet. Run 'Run Initial Router' first.")
            return
        if not self.target:
            messagebox.showwarning("No Target", "No target destination set.")
            return
        self.stop_movement()
        threading.Thread(target=self._reroute_thread, daemon=True).start()

    def _reroute_thread(self):
        """Threaded function to handle rerouting from current position without clearing previous routes."""
        try:
            current = self.current_node
            target = self.target
            
            traffic_data = simulate_random_traffic(self.graph)
            apply_traffic_to_graph(self.graph, traffic_data)
            
            res = construct_route(self.graph, current, target, vehicle_type=self.vehicle_type.get())
            self.street_names = res["street_names"]
            if not res["route_nodes"]:
                self.root.after(0, lambda: messagebox.showerror("No Route","No valid route found from current position."))
                return

            self.current_route = res
            self.current_position_index = 0
            
            color_index = (self.step_count) % len(self.replan_colors)
            replan_color = self.replan_colors[color_index]
            node_route = convert_edge_route_to_node_route(self.graph, res["route_enodes"])

            self.root.after(0, lambda: self.visualizer.plot_route(
                node_route, color=replan_color, label=f"Reroute {self.step_count + 1}"))
            self.root.after(1000, self.start_movement) 
            
            self._log_event(self.street_names[0], self.street_names[-1], res["total_time"], res["penalty"], len(res["route_nodes"]), "reroute-from-current")
            
            self.step_count += 1
            self.status_label.config(text=f"Rerouted from current position. Starting movement on new route...")
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to reroute: {str(e)}"))

    def _run_initial_thread(self, start, target):
        """Threaded function to run the initial route planning algorithm."""
        try:
            EG = self.graph
            self.step_count = 0
            self.current_position_index = 0

            res = construct_route(EG, start, target, vehicle_type=self.vehicle_type.get())
            self.street_names = res["street_names"]
            self.current_route = res
            if not res["route_nodes"]:
                self.root.after(0, lambda: messagebox.showerror("No Route", "No valid route found."))
                return
            
            node_route = convert_edge_route_to_node_route(EG, res["route_enodes"])
            self.root.after(0, lambda: self.visualizer.reset(route_nodes=node_route))

            reason = "initial" if res["penalty"] == 0 else "initial-with-penalty"
            self._log_event(self.street_names[0], self.street_names[-1], res["total_time"], res["penalty"], len(res["route_nodes"]), reason)
            
            self.current_node = start
            self.initial_planned = True

            self.root.after(0, self.start_movement_after_planning)
            self.status_label.config(text=f"Route planned successfully. Starting movement...")         
        except Exception as e:
            error_msg = f"Failed to plan route: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

    def run_initial(self):
        """    
        Runs the initial route planning algorithm and starts movement simulation.
        Preserves existing routes unless cleared by the user.
        """
        if not self.graph:
            messagebox.showwarning("No map loaded", "Load map first.")
            return

        try:
            start = int(self.start_node.get())
            target = int(self.target_node.get())
        except ValueError:
            messagebox.showerror("Error", "Start and Target must be integers (OSM node IDs).")
            return

        self.target = target
        self.stop_movement()
        if self.current_route and len(self.visualizer.current_routes) > 0:
            messagebox.showinfo("New Route Planning", "Previous routes will be cleared from the map displayed.")
        
        threading.Thread(target=self._run_initial_thread, args=(start, target), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = UserInterface(root)
    root.mainloop()
