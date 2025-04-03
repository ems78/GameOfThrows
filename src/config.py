# Neo4j Database Configuration
NEO4J = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "gameofthrows"
}

# Data Configuration
DATA = {
    "dataset_path": "data/lichess_games.pgn",
    "sample_size": 1000  # Number of games to process (set to None for all games)
}

# Blunder Detection Configuration
BLUNDER = {
    "evaluation_threshold": 200,  # Centipawn threshold for detecting blunders
    "stockfish_path": None,  # Path to Stockfish executable (optional)
    "analysis_depth": 15     # Depth for Stockfish analysis
}

# Analysis Configuration
ANALYSIS = {
    "community_detection_algorithm": "louvain",
    "min_blunder_count": 5  # Minimum number of blunders to consider a pattern
}

# Visualization Configuration
VISUALIZATION = {
    "node_size_factor": 5,
    "edge_width_factor": 0.5,
    "community_colors": ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"]
} 
