import pandas as pd
import kagglehub
from .db_manager import Neo4jConnection
from .models import GraphModels
from ..blunder_detection.blunder_detection import BlunderDetection
import datetime
import uuid

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
            game_id = game['id']

            # if game id in database, skip
            if models.find_game_by_id(game_id):
                continue

            date = pd.to_datetime(game['created_at']/1000, unit='s', origin='unix')
            time_control = game['increment_code']
            result = f"{game['winner']} won by {game['victory_status']}" if game['winner'] != '' else "draw"
            eco_code = game['opening_eco']
            pgn = game['moves']
            blunder_data = BlunderDetection.analyze_game_for_blunders(pgn)

            # If there is an error, stop the import
            if blunder_data.get("error"):
                print(f"Error analyzing game {game_id}: {blunder_data['error']}")
                return

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

            for blunder in blunder_data:
                if blunder['move_class'] == 'Blunder':
                    blunder_id = str(uuid.uuid4()) # Convert UUID to string for Neo4j
                    
                    # Create blunder
                    models.create_blunder(
                        id=blunder_id,
                        move_number=blunder['move_number'],
                        move_notation=blunder['move_notation'],
                        position_fen=blunder['fen'],
                        eval=blunder['eval'],
                        eval_change=blunder['eval_change'],
                        severity='high' if abs(blunder['eval_change']) > 2 else 'medium'
                    )
                    
                    # Connect blunder to game
                    models.connect_blunder_to_game(
                        blunder_id=blunder_id,
                        game_id=game_id
                    )
                    
                    # Connect player to blunder
                    player_id = white_player_id if blunder['player'] == 'White' else black_player_id
                    models.connect_player_to_blunder(
                        player_id=player_id,
                        blunder_id=blunder_id,
                        timestamp=date
                    )
            
    print("Data import complete!")

