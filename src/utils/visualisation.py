import os
import csv
import tkinter as tk
import networkx as nx
from typing import List
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from tkinter import ttk

class RouteVisualizer:
    """For routes visualisation"""
    
    def __init__(self, EG: nx.DiGraph, G, label: str):
        """Initialize the RouteVisualizer with an edge-based graph."""
        self.EG = EG
        self.G = G
        self._label = label
        self.fig, self.ax = None, None
        self.current_routes = []
        self.route_legends = []
        self._base_plot()
        self.vehicle_marker = None
        self.current_vehicle_position = None

    def _base_plot(self):
        """Base plot with dual legend system (enhanced like visualize_graph)."""
        edge_colors = []
        edge_linewidths = []
        edge_styles = []
        edge_alphas = []
        edge_zorders = []

        self.traffic_legend_info = set()

        for u, v, k, data in self.G.edges(keys=True, data=True):
            color = '#999999'
            linewidth = 0.5
            linestyle = 'solid'
            alpha = 0.7
            zorder = 3
            label = 'Normal Road'

            if 'traffic_mult' in data and data['traffic_mult'] == 0.01:
                color = 'orange'
                linewidth = 2.5
                linestyle = 'dashed'
                alpha = 1.0
                zorder = 6
                label = 'Closed Road'

            elif 'traffic_mult' in data and data['traffic_mult'] > 1.0:
                color = 'red'
                linewidth = 2.0
                linestyle = 'dotted'
                alpha = 0.9
                zorder = 5
                label = 'High Traffic'

            elif data.get('tunnel') == 'yes':
                color = 'black'
                linewidth = 2.0
                linestyle = 'dashdot'
                alpha = 0.8
                zorder = 4
                label = 'Tunnel'

            elif data.get('bridge') == 'yes':
                color = 'blue'
                linewidth = 2.0
                linestyle = 'dashdot'
                alpha = 0.9
                zorder = 5
                label = 'Bridge'

            edge_colors.append(color)
            edge_linewidths.append(linewidth)
            edge_styles.append(linestyle)
            edge_alphas.append(alpha)
            edge_zorders.append(zorder)
            self.traffic_legend_info.add((label, color, linestyle, linewidth, alpha))

        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        for (u, v, data), color, linewidth, linestyle, alpha, zorder in zip(
            self.G.edges(data=True), edge_colors, edge_linewidths, edge_styles, edge_alphas, edge_zorders
        ):
            u_x, u_y = self.G.nodes[u]['x'], self.G.nodes[u]['y']
            v_x, v_y = self.G.nodes[v]['x'], self.G.nodes[v]['y']

            self.ax.plot(
                [u_x, v_x],
                [u_y, v_y],
                color=color,
                linewidth=linewidth,
                linestyle=linestyle,
                alpha=alpha,
                zorder=zorder
            )

        self.ax.set_facecolor('white')
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_title(self._label)

        traffic_legend_elements = []
        for label, color, linestyle, linewidth, alpha in sorted(self.traffic_legend_info):
            traffic_legend_elements.append(
                mpatches.Patch(
                    color=color,
                    label=label,
                    linestyle=linestyle,
                    linewidth=linewidth,
                    alpha=alpha
                )
            )

        traffic_legend = self.ax.legend(
            handles=traffic_legend_elements,
            loc='upper left',
            bbox_to_anchor=(1, 1),
            fontsize=8,
            title="Road Properties & Traffic",
            title_fontsize=9,
            frameon=True,
            fancybox=True,
            shadow=True
        )

        self.ax.add_artist(traffic_legend)
        plt.tight_layout()

    def plot_route(self, route_nodes: List[int], color: str = "#E81111C4", label: str = None):
        """Draw a route on the plot without erasing previous routes."""
        if not route_nodes or self.ax is None:
            return
        
        xs, ys = [], []
        for i in range(len(route_nodes) - 1):
            u, v = route_nodes[i], route_nodes[i + 1]
            u_x, u_y = self.G.nodes[u]['x'], self.G.nodes[u]['y']
            v_x, v_y = self.G.nodes[v]['x'], self.G.nodes[v]['y']
            if not xs:
                xs.append(u_x)
                ys.append(u_y)
            xs.append(v_x)
            ys.append(v_y)
        
        if xs:
            line = self.ax.plot(
                xs, ys, 
                color=color, 
                linewidth=4.0, 
                alpha=0.9,
                zorder=10,
                solid_capstyle='round'
            )[0]
            
            start_marker = self.ax.scatter(
                xs[0], ys[0],
                c=color, 
                marker="o", 
                s=120,
                edgecolor='white',
                linewidth=2,
                zorder=11
            )
    
            end_marker = self.ax.scatter(
                xs[-1], ys[-1],
                c=color, 
                marker="X", 
                s=120,
                edgecolor='white',
                linewidth=2,
                zorder=11
            )
            
            route_markers = [line, start_marker, end_marker]
            self.current_routes.append(route_markers)
            if label:
                existing_index = -1
                for i, (existing_color, existing_label) in enumerate(self.route_legends):
                    if existing_label == label:
                        existing_index = i
                        break
                
                if existing_index >= 0:
                    self.route_legends[existing_index] = (color, label)
                else:
                    self.route_legends.append((color, label))
                self._update_route_legend()
            
            if plt.fignum_exists(self.fig.number):
                self.fig.canvas.draw()

    def _update_route_legend(self):
        """Completely rebuild the route legend from current route_legends."""
        if not self.route_legends:
            for artist in self.ax.get_children():
                if hasattr(artist, 'get_label') and artist.get_label() == '_route_legend':
                    artist.remove()
            return

        route_legend_elements = []
        for color, label in self.route_legends:
            route_legend_elements.append(
                plt.Line2D(
                    [0], [0],
                    color=color,
                    linewidth=3,
                    label=f"{label} (Route)"
                )
            )

            route_legend_elements.append(
                plt.Line2D(
                    [0], [0],
                    color=color,
                    marker='o',
                    markersize=8,
                    markeredgecolor='white',
                    markeredgewidth=1,
                    markerfacecolor=color,
                    linestyle='None',
                    label=f"{label} (Start)"
                )
            )

            route_legend_elements.append(
                plt.Line2D(
                    [0], [0],
                    color=color,
                    marker='X',
                    markersize=8,
                    markeredgecolor='white',
                    markeredgewidth=1,
                    markerfacecolor=color,
                    linestyle='None',
                    label=f"{label} (End)"
                )
            )

        for artist in self.ax.get_children():
            if hasattr(artist, 'get_label') and artist.get_label() == '_route_legend':
                artist.remove()

        route_legend = self.ax.legend(
            handles=route_legend_elements,
            loc='upper left',
            bbox_to_anchor=(1, 0.8),
            fontsize=8,
            title="Routes & Markers",
            title_fontsize=9,
            frameon=True,
            fancybox=True,
            shadow=True
        )
        route_legend.set_label('_route_legend')

    def update_vehicle_position(self, node_id, color="#00FF00", size=100):
        """Updates and visualize the vehicle's current position."""
        if self.vehicle_marker is not None:
            self.vehicle_marker.remove()
        
        node_x = self.G.nodes[node_id]['x']
        node_y = self.G.nodes[node_id]['y']
        self.vehicle_marker = self.ax.scatter(
            node_x, node_y,
            c=color,
            marker="o",
            s=size,
            edgecolor='white',
            linewidth=2,
            zorder=12,
            label="Current Vehicle Position"
        )
        
        self.current_vehicle_position = node_id
        if plt.fignum_exists(self.fig.number):
            self.fig.canvas.draw()

    def reset(self, route_nodes=None):
        """Clear all routes and optionally plot a new one."""
        for route_markers in self.current_routes:
            for artist in route_markers:
                if artist in self.ax.get_children():
                    artist.remove()
        self.current_routes = []
        self.route_legends = []
        
        if route_nodes:
            self.plot_route(route_nodes, color="#E6131382", label="Initial Route")
        if self.fig and plt.fignum_exists(self.fig.number):
            self.fig.canvas.draw()

    def close_map(self):
        if self.fig and plt.fignum_exists(self.fig.number):
            plt.close(self.fig)
            print("Map window closed")

    def clear_routes(self):
        self.reset()

    def clear_vehicle_position(self):
        """Clears the vehicle marker"""
        if self.vehicle_marker is not None:
            self.vehicle_marker.remove()
            self.vehicle_marker = None
            self.current_vehicle_position = None
            if plt.fignum_exists(self.fig.number):
                self.fig.canvas.draw()

    def display_map(self):
        """Display the map window."""
        if self.fig:
            plt.show(block=False)
            plt.pause(0.1)

class RoutingLogTable(ttk.Frame):
    """For displaying route logs"""

    def __init__(self, parent, log_file_path):
        super().__init__(parent)
        self.log_file_path = log_file_path
        self.log_data = []
        self._setup_table()
        self.load_logs()
        
    def _setup_table(self):
        """Sets up the table display structure"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=1, pady=1)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=('timestamp', 'start', 'target', 'total_time', 'penalty', 'route_length', 'reason'),
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=4
        )
        
        columns = [
            ('timestamp', 'Timestamp', 130),
            ('start', 'Start', 150),
            ('target', 'Target', 150),
            ('total_time', 'Total Time (s)', 70),
            ('penalty', 'Penalty (s)', 70),
            ('route_length', 'Route Length (KM)', 70),
            ('reason', 'Reason', 90)
        ]

        for col_id, heading, width in columns:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor=tk.CENTER)
        
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self._add_context_menu()

    def _add_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Refresh Logs", command=self.load_logs)
        self.context_menu.add_command(label="Clear Table", command=self.clear_table)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
                    
    def clear_table(self):
        """Clears the table rows"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.log_data = []
        
    def load_logs(self):
        """Loads routing logs from CSV file"""
        self.clear_table()
        if not os.path.exists(self.log_file_path):
            return
            
        try:
            with open(self.log_file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader, None) 
                for row in reader:
                    if len(row) >= 7:
                        self.log_data.append(row)
                        self.tree.insert('', 'end', values=row)
        except Exception as e:
            print(f"Error loading logs: {e}")
            
    def add_log_entry(self, log_entry):
        """Adds a new log entry to the table."""
        if len(log_entry) >= 7:
            self.tree.insert('', 0, values=log_entry)
            self.log_data.insert(0, log_entry)
            if len(self.log_data) > 50:
                for _ in range(len(self.log_data) - 50):
                    oldest = self.tree.get_children()[-1]
                    self.tree.delete(oldest)
                    self.log_data.pop()

"""
Helper functions
"""

def visualize_graph(graph, map_label):
    """Enhanced visualization with controlled transparency and layering"""
    edge_colors = []
    edge_linewidths = []
    edge_styles = []
    edge_alphas = []
    edge_zorders = []
    
    legend_info = set()
    for u, v, k, data in graph.edges(keys=True, data=True):
        color = '#999999'
        linewidth = 0.8
        linestyle = 'solid'
        alpha = 0.7
        zorder = 3 
        label = 'Normal Road'
        
        if 'traffic_mult' in data and data['traffic_mult'] == 0.01:
            color = 'orange'
            linewidth = 2.5
            linestyle = 'dashed'
            alpha = 1.0
            zorder = 6
            label = 'Closed Road'
            
        elif 'traffic_mult' in data and data['traffic_mult'] > 1.0:
            color = 'red'
            linewidth = 2.0
            linestyle = 'dotted' 
            alpha = 0.9
            zorder = 5 
            label = 'High Traffic'
            
        elif data.get('tunnel') == 'yes':
            color = 'black'
            linewidth = 2.0
            linestyle = 'dashdot'
            alpha = 0.8
            zorder = 4
            label = 'Tunnel'
            
        elif data.get('bridge') == 'yes':
            color = 'blue'
            linewidth = 2.0
            linestyle = 'dashdot'
            alpha = 0.9
            zorder = 5
            label = 'Bridge'
        
        edge_colors.append(color)
        edge_linewidths.append(linewidth)
        edge_styles.append(linestyle)
        edge_alphas.append(alpha)
        edge_zorders.append(zorder)
        legend_info.add((label, color, linestyle, linewidth, alpha))

    fig, ax = plt.subplots(figsize=(12, 8))
    for (u, v, data), color, linewidth, linestyle, alpha, zorder in zip(
        graph.edges(data=True), edge_colors, edge_linewidths, edge_styles, edge_alphas, edge_zorders
    ):
        u_x, u_y = graph.nodes[u]['x'], graph.nodes[u]['y']
        v_x, v_y = graph.nodes[v]['x'], graph.nodes[v]['y']
        
        ax.plot(
            [u_x, v_x], 
            [u_y, v_y],
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
            alpha=alpha,
            zorder=zorder
        )
    
    ax.set_facecolor('white')
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(map_label)
    
    legend_elements = []
    for label, color, linestyle, linewidth, alpha in sorted(legend_info):
        legend_elements.append(
            mpatches.Patch(
                color=color,
                label=label,
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=alpha
            )
        )
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), fontsize=8)
    plt.tight_layout()
    plt.show()
    
    return graph, fig, ax

def convert_edge_route_to_node_route(EG: nx.DiGraph, edge_route: List[tuple]) -> List[int]:
    """Convert an edge-based route to a node-based route."""
    if not edge_route:
        return []
    node_route = []
    first_edge = edge_route[0]
    node_route.append(EG.nodes[first_edge]['orig_u'])
    for edge in edge_route:
        node_route.append(EG.nodes[edge]['orig_v'])
    return node_route
