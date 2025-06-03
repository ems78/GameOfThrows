# Game of Throws

A network analysis project that explores chess game data as a graph network using Neo4j.

## Project Overview
This project analyzes chess game data to discover patterns in player behavior, game dynamics, and strategic choices using network analysis. By representing chess games as a complex network, we can identify relationships between players, their playing styles, and the evolution of chess strategies over time.

## Problem Statement

### Research Questions
1. **Temporal Network Evolution**
   - How do player networks evolve over time? Do we see the emergence of distinct "eras" in chess strategy?
   - Can we identify "tipping points" where certain openings or strategies become dominant?
   - How does the time control (increment) affect the network structure of games?

2. **Player Performance and Network Position**
   - Do players who frequently play against higher-rated opponents improve faster than those who don't?
   - Can we predict a player's rating progression based on their network position and game history?
   - How does a player's network position (centrality, clustering coefficient) correlate with their win rate against similarly rated opponents?

3. **Opening Theory and Network Analysis**
   - Can we identify "gateway openings" that lead to specific types of positions or outcomes?
   - How do opening choices create distinct communities of players?
   - Can we predict game outcomes based on the opening phase network structure?

4. **Game Dynamics and Network Properties**
   - How do different time controls (e.g., 5+10 vs 10+0) affect the network structure of games?
   - Can we identify patterns in how games end (resignation, checkmate, timeout) based on network metrics?
   - Do certain network positions correlate with more decisive or drawn games?

### Significance
This research is significant for both database and network analysis because:

1. **Database Perspective**
   - Demonstrates how to model and query complex temporal relationships in a graph database
   - Shows how to efficiently analyze large-scale game data with multiple attributes
   - Illustrates the importance of proper data modeling for time-series network analysis

2. **Network Analysis Perspective**
   - Applies temporal network theory to understand the evolution of competitive games
   - Uses graph metrics to analyze player development and strategy evolution
   - Demonstrates how network analysis can reveal hidden patterns in competitive systems

3. **Practical Applications**
   - Could help players understand their development path and optimal training strategies
   - May improve rating systems by incorporating network-based metrics
   - Could help tournament organizers optimize pairings and time controls
   - Provides insights into how competitive systems evolve over time

### Features

- Graph database of chess players, games, and openings
- Temporal network analysis of player interactions
- Opening usage and popularity analysis
- Player performance metrics and rating progression
- Community detection in the player network
- Interactive and static visualizations

### Project Structure

```
├── data/                  # Directory for chess game dataset
├── src/
│   ├── main.py           # Main entry point for data import and analysis
│   ├── config.py         # Configuration settings
│   ├── modules/
│   │   ├── analysis/     # Analysis algorithms and metrics
│   │   ├── database/     # Neo4j database interaction
│   │   │   ├── db_manager.py    # Database connection management
│   │   │   ├── models.py        # Data models and CRUD operations
│   │   │   ├── queries.py       # Analysis queries
│   │   │   ├── import_data.py   # Data import functionality
│   │   │   └── schema.cypher    # Database schema definition
│   │   └── visualization/       # Result visualization
│   │       └── network_visualization.py  # Network visualization tools
└── tests/                # Unit tests
```

### Setup Instructions

1. **Start Neo4j using Docker**
```bash
docker run --name neo4j-gameofthrows -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/gameofthrows -d neo4j:latest
```

2. **Create and activate Python virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Import dataset**
```bash
python main.py --import-data --batch-size 1000 --max-games 10000
```

5. **Access Neo4j Browser**
   Open your web browser and navigate to http://localhost:7474/
   - Username: neo4j
   - Password: gameofthrows

## Usage

### Data Import
```bash
# Import data with default settings
python main.py --import-data

# Import with custom batch size and game limit
python main.py --import-data --batch-size 1000 --max-games 10000

# Delete existing data before import
python main.py --import-data --delete-all
```

### Analysis and Visualization
```bash
# Generate all visualizations
python main.py --visualizations all

# Generate specific visualizations
python main.py --visualizations temporal opening

# Show visualizations on screen
python main.py --visualizations player community --show

# Customize visualization parameters
python main.py --visualizations opening --top-openings 15 --dpi 600
```

### Command Line Options

- `--import-data`: Import chess data to Neo4j
- `--batch-size`: Number of games to process in each batch (default: 1000)
- `--max-games`: Maximum number of games to import (default: all)
- `--delete-all`: Delete all existing data before import
- `--output-dir`: Directory to save visualizations (default: output)
- `--time-window`: Time window for temporal analysis (daily/weekly/monthly/yearly)
- `--top-openings`: Number of top openings to show (default: 10)
- `--dpi`: DPI for saved images (default: 300)
- `--show`: Show visualizations instead of saving them
- `--visualizations`: Which visualizations to generate (temporal/opening/player/community/all)

## Output

Visualizations are saved as PNG files in the specified output directory:

- `temporal_network.png`: Evolution of player networks over time
- `opening_network.png`: Network of openings and their usage patterns
- `player_network.png`: Player network with rating progression
- `player_communities.png`: Communities of players based on game interactions

## Data

This project uses chess game data from Lichess.org. [You can download the dataset from Kaggle](https://www.kaggle.com/datasets/datasnaek/chess) or use your own PGN files.
