```markdown
# Emergency Routing System
Screenshot 2025-11-19 165735.png
https://github.com/Vincentius474/CA_Emergency_Routing_System/blob/main/Screenshot%202025-11-19%20165700.png


## Overview

The Emergency Routing System is a comprehensive Python application designed to provide intelligent route planning for emergency vehicles (ambulances, fire engines, and police units) in urban environments. The system incorporates real-world constraints, traffic simulation, and multiple pathfinding algorithms to generate optimal routes for emergency response scenarios.

## Features

- **Multi-Vehicle Support**: Custom routing profiles for ambulances, fire engines, and police units
- **Intelligent Route Planning**: Multiple search algorithms (Dijkstra, A*, Bidirectional A*) with constraint validation
- **Real-time Traffic Simulation**: Dynamic traffic conditions with random traffic multipliers
- **Interactive Visualization**: Real-time route visualization with vehicle movement simulation
- **Constraint Management**: Vehicle-specific constraints (height, weight, lane requirements, road types)
- **Route Logging**: Comprehensive logging of all routing events and performance metrics
- **Multi-City Support**: Pre-configured for major South African metropolitan areas
- **Dynamic Rerouting**: Manual rerouting from current vehicle position
- **Turn Cost Calculations**: Realistic routing with turn penalties and angle-based costs

## System Architecture

### Core Components

1. **User Interface** (`main.py`)
   - Tkinter-based control panel
   - Real-time status monitoring
   - Interactive map visualization
   - Route logging table

2. **Route Planning** (`route_planner.py`)
   - Main route construction logic
   - Progressive constraint relaxation
   - Multi-algorithm route evaluation

3. **Search Algorithms** (`search_algorithms.py`)
   - Dijkstra's algorithm
   - A* search with heuristics
   - Bidirectional A* search
   - Edge-based graph traversal

4. **Constraint Management** (`constraints.py`)
   - Vehicle-specific constraint definitions
   - Route validation against constraints
   - Traffic simulation and application

5. **Graph Construction** (`graph_constructor.py`)
   - OSM data processing
   - Edge-based graph creation
   - Turn cost calculations

6. **OSM Data Loading** (`osm_loader.py`)
   - OpenStreetMap data retrieval
   - GraphML file management
   - Subset area processing

7. **Visualization** (`visualisation.py`)
   - Route plotting and animation
   - Vehicle position tracking
   - Interactive map legends

8. **Graph Utilities** (`graph_utils.py`)
   - Graph loading and manipulation
   - Travel time calculations
   - Route validation helpers

## Installation & Setup

### Prerequisites

```bash
pip install networkx osmnx matplotlib pandas numpy
```

### System Requirements
- Python 3.7+
- 4GB RAM minimum
- Internet connection for initial OSM data download
- 500MB disk space for map data

### Data Preparation

1. The system automatically downloads OSM data for specified cities
2. Graph files are cached in the `../data/` directory
3. Pre-configured cities include:
   - Johannesburg
   - Tshwane (Pretoria)
   - Ekurhuleni
   - Polokwane
   - Durban
   - Cape Town

## Usage

### Starting the Application

```bash
python main.py
```

### Basic Workflow

1. **Setup System**: Load map data for selected city
2. **Select Vehicle**: Choose ambulance, fire engine, or police unit
3. **Initiate Respond**: System automatically selects random start and target nodes
4. **Monitor Movement**: Watch real-time vehicle movement on the map
5. **Manual Reroute**: Trigger dynamic rerouting from current position

### Key Controls

- **Setup System**: Load and initialize map data
- **System Reset**: Clear all routes and reset state
- **Initiate Respond**: Start new emergency response route
- **Manual Reroute**: Recalculate route from current position

## Vehicle Profiles

### Ambulance
- Max height: 3.0m
- Max weight: 4.0 tons
- Minimum lanes: 1
- Avoids closed roads
- Moderate traffic sensitivity
- Preferred road types: primary, secondary, tertiary, residential

### Fire Engine
- Max height: 3.5m
- Max weight: 12.0 tons
- Minimum lanes: 2
- Avoids closed roads
- High traffic sensitivity
- Preferred road types: primary, secondary, tertiary, residential

### Police Units
- Max height: 2.5m
- Max weight: 2.5 tons
- Minimum lanes: 1
- Can use closed roads
- High traffic sensitivity
- Preferred road types: primary, secondary, tertiary, residential

## Algorithm Details

### Search Algorithms
- **Dijkstra**: Guaranteed shortest path, no heuristics
- **A***: Heuristic-based optimization for faster computation
- **Bidirectional A***: Simultaneous forward/backward search

### Constraint Relaxation
The system progressively relaxes constraints when no valid route is found:
- Level 0: Original constraints
- Level 1: Remove road type and traffic constraints
- Level 2: Remove lane requirements
- Level 3: Keep only closed road avoidance

## File Structure

```
emergency-routing-system/
├── main.py                 # Main application entry point
├── core/
│   ├── route_planner.py    # Route planning logic
│   ├── constraints.py      # Vehicle constraints definition
│   └── search_algorithms.py # Pathfinding algorithms
├── data_input/
│   ├── osm_loader.py       # OSM data loading
│   └── graph_constructor.py # Graph construction
├── src/
│   └── utils/
│       ├── visualisation.py # Visualization components
│       └── graph_utils.py   # Graph utility functions
├── data/                   # Data directory (created automatically)
│   ├── route_logs/         # Routing logs
│   └── *.graphml           # OSM graph files
└── README.md
```

## Data Files

### Input Files
- OSM GraphML files (`*.graphml`)
- Edge graph pickle files (`*_edgegraph.gpickle`)

### Output Files
- Route logs (`routing_log.csv`)
- Route directions (`route_directions_log.csv`)
- Visualization maps

## Configuration

### Supported Cities
- City of Johannesburg Metropolitan Municipality
- City of Tshwane Metropolitan Municipality  
- City of Ekurhuleni Metropolitan Municipality
- City of Polokwane Capricorn District Municipality
- City of Durban eThekwini Metropolitan
- City of Cape Town Western Cape

### Customization
Modify `VEHICLE_PROFILES` in `constraints.py` to add new vehicle types or adjust constraints.

## Performance Features

- Multi-threaded route planning
- Efficient edge-based graph representation
- Intelligent caching of map data
- Real-time visualization updates
- Comprehensive logging and analytics

## Troubleshooting

### Common Issues

1. **Map Loading Failures**
   - Check internet connection for OSM data download
   - Verify data directory permissions
   - Ensure sufficient disk space

2. **Route Planning Timeouts**
   - Try using subset maps for testing
   - Reduce graph complexity in dense urban areas
   - Check system memory availability

3. **Visualization Problems**
   - Verify matplotlib backend compatibility
   - Check display permissions for GUI
   - Ensure proper Tkinter installation

4. **Missing Dependencies**
   ```bash
   pip install --upgrade networkx osmnx matplotlib pandas numpy
   ```

## Development

### Extending the System

- Add new vehicle types in `constraints.py`
- Implement additional search algorithms in `search_algorithms.py`
- Create custom visualization themes in `visualisation.py`
- Add new city configurations in the UI combobox values

### Testing
Run individual components:
```bash
python -m data_input.osm_loader
python -m data_input.graph_constructor
python -m core.route_planner
```

### Adding New Cities
1. Update city list in `main.py` UserInterface class
2. Ensure proper OSM place name format
3. Run system to automatically download map data

## API Reference

### Main Functions

```python
# Route planning
construct_route(graph, start_node, target_node, vehicle_type)

# Graph loading
load_edge_graph(file_path)

# Visualization
RouteVisualizer(graph, original_graph, label)
```

### Key Classes
- `UserInterface`: Main application window
- `RouteVisualizer`: Map visualization and route plotting
- `RoutingLogTable`: Log display and management
- `OSMLoader`: OpenStreetMap data handling
- `GraphConstructor`: Graph processing and construction

## License

This project is intended for educational and research purposes in emergency response optimization.

## Acknowledgments

- OpenStreetMap for geographic data
- NetworkX for graph algorithms
- OSMnx for OSM data processing
- Matplotlib for visualization components

---

For questions or contributions, please refer to the component documentation in each source file.
```
