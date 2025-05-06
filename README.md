# Game of Throws

A network analysis project that explores chess blunders as a graph network using Neo4j.

## Project Overview
This project analyzes chess game data to discover patterns in how players make mistakes (blunders). By representing blunders as a network, we can identify relationships between players, their common mistakes, and the chess openings where these mistakes occur.

## Features
- Graph database of chess players, games, openings, and blunders
- Blunder community detection
- Blunder cascade analysis
- Opening analysis by blunder frequency
- Network visualization of blunder patterns

## Setup Instructions

### Prerequisites

- Docker
- Python 3.8+
- Neo4j Database
- Stockfish chess engine

### Installation

1. **Clone the repository**
```
git clone https://github.com/ems78/GameOfThrows.git
cd GameOfThrows
```

2. **Update configuration if needed**

   Located in `src/config.py`

3. **Start Neo4j using Docker**
 ```
docker run --name neo4j-gameofthrows -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/gameofthrows -d neo4j:latest
```

4. **Create and activate Python virtual environment**
```
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

5. **Install dependencies**
```
pip install -r requirements.txt
brew install stockfish
```

6. **Import dataset**
```
python import_chess_data.py
```

7. **Access Neo4j Browser**

   Open your web browser and navigate to http://localhost:7474/
   - Username: neo4j
   - Password: gameofthrows

## Project Structure
```
├── data/                  # Directory for chess game dataset
├── src/
│   ├── main.py            # Main entry point
│   ├── config.py          # Configuration settings
│   ├── modules/
│       ├── blunder_detection/   # Chess blunder detection algorithms
│       ├── database/            # Neo4j database interaction
│       ├── analysis/            # Network analysis algorithms
│       └── visualization/       # Result visualization
└── tests/                 # Unit tests
```

## Usage

Run the main script to generate visualization
```bash
# Generate all visualization with default settings
python main.py

# Show visualizations on screen instead of saving them
python main.py --show

# Generate only player network visualization with higher minimum edge weight
python main.py --visualization player --min-edge-weight 3

# Generate high-resolution opening blunder chart with more openings
python main.py --visualization opening --top-openings 15 --dpi 600

# Generate community visualization with larger minimum community size
python main.py --visualization community --min-community-size 5
```

## Command Line Options

- `--output-dir`: Directory to save visualizations (default: output)
- `--min-edge-weight`: Minimum edge weight for player blunder graph (default: 2)
- `--min-community-size`: Minimum size of communities to visualize (default: 3)
- `--top-openings`: Number of top openings to show (default: 10)
- `--dpi`: DPI for saved images (default: 300)
- `--show`: Show visualizations instead of saving them
- `--visualization`: Which visualizations to generate (choices: player, community, opening, all)

## Output

Visualizations are saved as PNG files in the specified output directory:

- `player_blunder_network.png`: Network of players connected by similar blunders
- `blunder_communities.png`: Communities of players with similar blunder patterns
- `opening_blunders.png`: Bar chart of openings with most blunders

## Data
This project uses chess game data from Lichess.org. [You can download the dataset from Kaggle](https://www.kaggle.com/datasets/datasnaek/chess) or use your own PGN files. 
