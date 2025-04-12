import pandas as pd
import kagglehub
from .db_manager import Neo4jConnection
from .models import GraphModels
from ..blunder_detection.blunder_detection import BlunderDetection
import datetime
import uuid
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
    blunder_detection = BlunderDetection()
    
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
            blunders_found = 0
            
            for _, game in batch.iterrows():
                game_id = game['id']

                # if game id in database, skip
                if models.find_game_by_id(game_id):
                    print(".", end="", flush=True)
                    continue

                date = pd.to_datetime(game['created_at']/1000, unit='s', origin='unix')
                time_control = game['increment_code']
                result = f"{game['winner']} won by {game['victory_status']}" if game['winner'] != '' else "draw"
                eco_code = game['opening_eco']
                pgn = game['moves']
                blunder_data = blunder_detection.analyze_game_for_blunders(pgn)

                # If None, stop import
                if blunder_data is None:
                    print("\nError analyzing game", game_id)
                    break

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

                game_blunders = 0
                for blunder in blunder_data:
                    if blunder['move_class'] == 'Blunder':
                        game_blunders += 1
                        blunder_id = str(uuid.uuid4()) # Convert UUID to string for Neo4j
                        
                        # Create blunder
                        models.create_blunder(
                            id=blunder_id,
                            move_number=blunder['move_number'],
                            move_notation=blunder['move_notation'],
                            best_move=blunder['bestmove'],
                            position_fen=blunder['fen'],
                            eval=blunder['eval'],
                            eval_change=blunder['eval_change'],
                            is_mate=blunder['is_mate'],
                            severity='high' if abs(blunder['eval_change']) > 2 or blunder['is_mate'] 
                                            else 'medium' if abs(blunder['eval_change']) > 1 
                                            else 'low'
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
                
                games_processed += 1
                blunders_found += game_blunders
                print(".", end="", flush=True)
                
                # Print a newline every 50 games for better readability
                if games_processed % 50 == 0:
                    print()
                    print(f"  {games_processed}/{len(batch)} games processed", end="", flush=True)
            
            print(f"\nBatch {batch_num} complete: {games_processed} games processed, {blunders_found} blunders found")
    finally:
        blunder_detection.close()
        db.close()

