# Game of Throws

A network analysis project that explores chess game data as a graph network using Neo4j.

## Project Overview
This project analyzes chess game data to discover patterns in player behavior and strategic choices using network analysis. By representing chess games as a complex network, we can identify relationships between players, their network positions, and how these positions affect their performance and development.

## Problem Statement

### Research Questions
1. **Player Performance and Network Position**
   - How does a player's network position (centrality, clustering coefficient) correlate with their win rate?
   - Can we identify patterns in how network position affects player development?
   - What network metrics best predict player performance?

2. **Opening Theory and Network Analysis**
   - Can we identify "gateway openings" that lead to specific types of positions or outcomes?
   - How do opening choices create distinct communities of players?
   - Can we identify patterns in opening usage and their impact on game outcomes?
   - What network structures emerge from opening choices?
   - Can we predict game outcomes based on the opening phase network structure?

### Significance
This research is significant for both database and network analysis because:

1. **Database Perspective**
   - Demonstrates how to model and query complex graph relationships in Neo4j
   - Shows how to efficiently analyze large-scale game data with multiple attributes
   - Illustrates the importance of proper data modeling for network analysis
   - Leverages Neo4j's native graph algorithms for performance metrics

2. **Network Analysis Perspective**
   - Applies network theory to understand player development and performance
   - Uses graph metrics to analyze player relationships and communities
   - Demonstrates how network analysis can reveal hidden patterns in competitive systems
   - Shows the impact of network position on player success

3. **Practical Applications**
   - Could help players understand their development path and optimal training strategies
   - May improve rating systems by incorporating network-based metrics
   - Could help tournament organizers optimize pairings
   - Provides insights into how network position affects player performance

### Features

- Graph database of chess players, games, and openings
- Network position analysis of player interactions
- Opening usage and popularity analysis
- Player performance metrics and rating progression
- Community detection in the player network
- Interactive and static visualizations

### Project Structure

```
├── data/                  # Directory for chess game dataset
├── src/
│   ├── config.py         # Configuration settings
│   ├── analysis.py       # Analysis algorithms and metrics
│   ├── visualization.py  # Result visualization
│   └── database/         # Neo4j database interaction
│       ├── db_manager.py    # Database connection management
│       ├── models.py        # Data models and CRUD operations
│       ├── import_data.py   # Data import functionality
│       └── schema.cypher    # Database schema definition
└── main.py               # Main entry point for data import and analysis
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
python main.py --analyze
```

### Command Line Options

- `--import-data`: Import chess data to Neo4j
- `--batch-size`: Number of games to process in each batch (default: 1000)
- `--max-games`: Maximum number of games to import (default: all)
- `--delete-all`: Delete all existing data before import
- `--output-dir`: Directory to save visualizations (default: output)
- `--output-format`: Output format for visualizations (png/pdf/svg)
- `--dpi`: DPI for saved images (default: 300)
- `--show`: Show visualizations
- `--analyze`: Analyze network position and trends in opening usage

## Output

Visualizations are saved as PNG files in the specified output directory:

- `game_dynamics.png`: Breaks down game outcomes by victory status (mate, resign, outoftime, draw), showing average game length and rating differences for each type.
- `gateway_openings.png`: Identifies and analyzes openings that frequently transition to other openings, showing their centrality in the opening network and win rates by color.
- `network_metrics.png`: Displays the relationship between network centrality/clustering and win rates, helping identify how network position affects player performance.
- `opening_communities.png`: Shows how players cluster based on their opening choices, including community sizes, average ratings, and common openings within each community.
- `opening_network_position.png`: Visualizes how openings are connected in the network, showing win rates vs games played and identifying the most influential openings.
- `opening_performance.png`: Analyzes opening statistics including most played openings, win rates vs game length, and overall opening performance metrics.
- `rating_progression.png`: Shows player rating distribution, rating changes, and performance patterns across different rating ranges. Includes analysis of top players and their performance metrics.

## Data

This project uses chess game data from Lichess.org. [You can download the dataset from Kaggle](https://www.kaggle.com/datasets/datasnaek/chess) or use your own PGN files.
