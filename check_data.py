#!/usr/bin/env python3
from src.modules.database.db_manager import Neo4jConnection

def check_database_data():
    """Check if there's any data in the database"""
    db = Neo4jConnection()
    
    # Check for players
    players_query = "MATCH (p:Player) RETURN count(p) as player_count"
    players_result = db.query(players_query)
    player_count = players_result[0]['player_count'] if players_result else 0
    print(f"Number of players in database: {player_count}")

    # Check for games
    games_query = "MATCH (g:Game) RETURN count(g) as game_count"
    games_result = db.query(games_query)
    game_count = games_result[0]['game_count'] if games_result else 0
    print(f"Number of games in database: {game_count}")
    
    # Check for blunders
    blunders_query = "MATCH (b:Blunder) RETURN count(b) as blunder_count"
    blunders_result = db.query(blunders_query)
    blunder_count = blunders_result[0]['blunder_count'] if blunders_result else 0
    print(f"Number of blunders in database: {blunder_count}")
    
    # Check for player-blunder relationships
    relationships_query = """
    MATCH (p:Player)-[:MADE_BLUNDER]->(b:Blunder)
    RETURN count(*) as relationship_count
    """
    relationships_result = db.query(relationships_query)
    relationship_count = relationships_result[0]['relationship_count'] if relationships_result else 0
    print(f"Number of player-blunder relationships: {relationship_count}")
    
    # Check for shared blunders
    shared_blunders_query = """
    MATCH (p1:Player)-[:MADE_BLUNDER]->(b1:Blunder)
    MATCH (p2:Player)-[:MADE_BLUNDER]->(b2:Blunder)
    WHERE p1 <> p2 AND b1.position_fen = b2.position_fen
    RETURN count(DISTINCT [p1, p2]) as shared_blunders_count
    """
    shared_blunders_result = db.query(shared_blunders_query)
    shared_blunders_count = shared_blunders_result[0]['shared_blunders_count'] if shared_blunders_result else 0
    print(f"Number of player pairs with shared blunders: {shared_blunders_count}")
    
    db.close()

if __name__ == "__main__":
    check_database_data() 
