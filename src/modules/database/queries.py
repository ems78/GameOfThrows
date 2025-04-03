import pandas as pd
import kagglehub
from .db_manager import Neo4jConnection
from .models import GraphModels
import datetime
import chess
import chess.pgn
import io
import uuid
import re

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

def import_data_to_neo4j(batch_size=1000, max_games=None):
    """
    Import chess data from Kaggle dataset to Neo4j
    
    Args:
        batch_size: Number of games to process in each batch
        max_games: Maximum number of games to import (None for all)
    """
    db = Neo4jConnection()
    models = GraphModels()
    
    # Download and load data
    df = load_chess_data()
    
    # Limit number of games if specified
    if max_games and max_games < len(df):
        df = df.iloc[:max_games]
    
    print(f"Importing {len(df)} games to Neo4j...")
    
    # Process in batches
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")
        
        for _, game in batch.iterrows():
            # Create or update game
            game_id = game['id']
            date = pd.to_datetime(game['created_at']/1000, unit='s', origin='unix')
            time_control = game['increment_code']
            result = f"{game['winner']} won by {game['victory_status']}" if game['winner'] != '' else "draw"
            pgn = game['moves']
            eco_code = game['opening_eco']
            
            # Create game
            models.create_game(
                id=game_id,
                date=date,
                time_control=time_control,
                result=result,
                pgn=pgn,
                eco_code=eco_code
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
            
            # Create players
            white_player_id = game['white_id']
            black_player_id = game['black_id']
            
            models.create_player(
                id=white_player_id, 
                username=white_player_id,  # player id is username
                rating=game['white_rating']
            )
            
            models.create_player(
                id=black_player_id,
                username=black_player_id,  # player id is username
                rating=game['black_rating']
            )
            
            # Connect players to game
            models.connect_player_to_game(
                player_id=white_player_id,
                game_id=game_id,
                color="white",
                rating_at_game=game['white_rating']
            )
            
            models.connect_player_to_game(
                player_id=black_player_id,
                game_id=game_id,
                color="black",
                rating_at_game=game['black_rating']
            )
            
            # TODO: Identify blunders
    
    print("Data import complete!")

