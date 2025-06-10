from .db_manager import Neo4jConnection

class GraphModels:
    def __init__(self):
        self.db = Neo4jConnection()

    #  For testing imports
    def delete_all_data(self):
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        return self.db.query(query)
    
    def create_player(self, id, username, rating):
        query = """
        MERGE (p:Player {id: $id}) 
        ON CREATE SET 
            p.username = $username,
            p.rating = $rating
        RETURN p
        """
        return self.db.query(query, {
            'id': id,
            'username': username,
            'rating': rating
        })
    
    def create_game(self, id, rated, created_at, last_move_at, turns, victory_status, winner, increment_code, moves):
        query = """
        MERGE (g:Game {id: $id})
        ON CREATE SET 
            g.rated = $rated,
            g.created_at = $created_at,
            g.last_move_at = $last_move_at,
            g.turns = $turns,
            g.victory_status = $victory_status,
            g.winner = $winner,
            g.increment_code = $increment_code,
            g.moves = $moves
        RETURN g
        """
        return self.db.query(query, {
            'id': id,
            'rated': rated,
            'created_at': created_at,
            'last_move_at': last_move_at,
            'turns': turns,
            'victory_status': victory_status,
            'winner': winner,
            'increment_code': increment_code,
            'moves': moves
        })

    
    def find_game_by_id(self, id):
        query = """
        MATCH (g:Game {id: $id})
        RETURN g
        """
        return self.db.query(query, {'id': id})

    def create_opening(self, eco_code, name, ply):
        query = """
        MERGE (o:Opening {eco_code: $eco_code})
        ON CREATE SET 
            o.name = $name,
            o.ply = $ply
        RETURN o
        """
        return self.db.query(query, {
            'eco_code': eco_code,
            'name': name,
            'ply': ply
        })
    
    def connect_player_to_game(self, player_id, game_id, color, rating_at_game):
        query = """
        MATCH (p:Player {id: $player_id})
        MATCH (g:Game {id: $game_id})
        MERGE (p)-[r:PLAYED_IN {
            color: $color, 
            rating_at_game: $rating_at_game
        }]->(g)
        RETURN r
        """
        return self.db.query(query, {
            'player_id': player_id,
            'game_id': game_id,
            'color': color,
            'rating_at_game': rating_at_game
        })

    def connect_game_to_opening(self, game_id, opening_eco):
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (o:Opening {eco_code: $eco_code})
        MERGE (g)-[:USES]->(o)
        RETURN g, o
        """
        return self.db.query(query, {
            'game_id': game_id,
            'eco_code': opening_eco
        })
