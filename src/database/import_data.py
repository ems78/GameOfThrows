import pandas as pd
import kagglehub
from .db_manager import Neo4jConnection
from .models import GraphModels
import datetime
# import uuid
import sys

def download_chess_dataset():
    """Download chess dataset from Kaggle"""
    path = kagglehub.dataset_download("datasnaek/chess")
    print(f"Dataset downloaded to: {path}")
    return path

def load_chess_data():
    """Load chess data from Kaggle dataset into pandas DataFrame"""
    path = download_chess_dataset()
    df = pd.read_csv(f"{path}/games.csv")
    print(f"Loaded {len(df)} chess games")
    return df

#  For testing imports
def delete_all_data():
    """Delete all data from Neo4j"""
    db = Neo4jConnection()
    models = GraphModels()
    models.delete_all_data()

def import_data_to_neo4j(batch_size=1000, max_games=None):
    """
    Import chess data from Kaggle dataset to Neo4j
    
    Args:
        batch_size: Number of games to process in each batch
        max_games: Maximum number of games to import (None for all)
    """
    print("Initializing database connection and models...")
    db = Neo4jConnection()
    models = GraphModels()
    
    try:
        # Download and load data
        df = load_chess_data()
        
        # Limit number of games if specified
        if max_games and max_games < len(df):
            df = df.iloc[:max_games]
        
        total_games = len(df)
        total_batches = (total_games - 1) // batch_size + 1
        print(f"Starting import of {total_games} games in {total_batches} batches...")
        
        # Process in batches
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_num = i//batch_size + 1
            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} games)")
            print("Importing games: ", end="", flush=True)
            
            games_processed = 0
            
            for _, game in batch.iterrows():
                game_id = game['id']

                # if game id in database, skip
                if models.find_game_by_id(game_id):
                    print(".", end="", flush=True)
                    continue

                # Store timestamps as Unix timestamps (milliseconds)
                created_at = int(game['created_at'])
                last_move_at = int(game['last_move_at'])

                # Create game
                models.create_game(
                    id=game_id,
                    rated=game['rated'],
                    created_at=created_at,
                    last_move_at=last_move_at,
                    turns=game['turns'],
                    victory_status=game['victory_status'],
                    winner=game['winner'],
                    increment_code=game['increment_code'],
                    moves=game['moves']
                )
                
                # Create opening
                models.create_opening(
                    eco_code=game['opening_eco'],
                    name=game['opening_name'],
                    ply=game['opening_ply']
                )
                
                # Connect game to opening
                models.connect_game_to_opening(
                    game_id=game_id,
                    opening_eco=game['opening_eco']
                )
                
                models.create_player(
                    id=game['white_id'], 
                    username=game['white_id'],  # player id is username
                    rating=game['white_rating']
                )
                
                models.create_player(
                    id=game['black_id'],
                    username=game['black_id'],  # player id is username
                    rating=game['black_rating']
                )
                
                # Connect players to game
                models.connect_player_to_game(
                    player_id=game['white_id'],
                    game_id=game_id,
                    color="white",
                    rating_at_game=game['white_rating']
                )
                
                models.connect_player_to_game(
                    player_id=game['black_id'],
                    game_id=game_id,
                    color="black",
                    rating_at_game=game['black_rating']
                )
                
                games_processed += 1
                print(".", end="", flush=True)
                
                # Print a newline every 50 games for better readability
                if games_processed % 50 == 0:
                    print()
                    print(f"  {games_processed}/{len(batch)} games processed", end="", flush=True)
            
            print(f"\nBatch {batch_num} complete: {games_processed} games processed")
    finally:
        db.close()
