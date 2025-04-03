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
- Stockfish chess engine (optional, for more accurate blunder detection)

### Installation

1. Clone the repository
```
git clone <repository-url>
cd GameOfThrows
```

2. **Start Neo4j using Docker**
   ```
   docker run --name neo4j-gameofthrows -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/gameofthrows -d neo4j:latest
   ```

3. **Create and activate Python virtual environment**
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Start Neo4j database

5. Configure the database connection in `config.py`

6. Run the data processing pipeline
```
python src/main.py
```

3. **Access Neo4j Browser**
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
│       ├── data_processing/     # Data import and processing
│       ├── blunder_detection/   # Chess blunder detection algorithms
│       ├── database/            # Neo4j database interaction
│       ├── analysis/            # Network analysis algorithms
│       └── visualization/       # Result visualization
└── tests/                 # Unit tests
```

## Data
This project uses chess game data from Lichess.org. You can download the dataset from Kaggle or use your own PGN files. 
