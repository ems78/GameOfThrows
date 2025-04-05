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
    
    def create_player(self, id, username, rating, country=None, account_creation_date=None):
        query = """
        MERGE (p:Player {id: $id}) 
        ON CREATE SET 
            p.username = $username,
            p.rating = $rating,
            p.country = $country,
            p.account_creation_date = $account_creation_date
        RETURN p
        """
        return self.db.query(query, {
            'id': id,
            'username': username,
            'rating': rating,
            'country': country,
            'account_creation_date': account_creation_date
        })
    
    def create_game(self, id, date, time_control, result, pgn, eco_code):
        query = """
        MERGE (g:Game {id: $id})
        ON CREATE SET 
            g.date = $date,
            g.time_control = $time_control,
            g.result = $result,
            g.pgn = $pgn,
            g.eco_code = $eco_code
        RETURN g
        """
        return self.db.query(query, {
            'id': id,
            'date': date,
            'time_control': time_control,
            'result': result,
            'pgn': pgn,
            'eco_code': eco_code
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
    
    def create_blunder(self, id, move_number, move_notation, position_fen, eval, eval_change, severity=None):
        query = """
        MERGE (b:Blunder {id: $id})
        ON CREATE SET 
            b.move_number = $move_number,
            b.move_notation = $move_notation,
            b.position_fen = $position_fen,
            b.eval = $eval,
            b.eval_change = $eval_change,
            b.severity = $severity
        RETURN b
        """
        return self.db.query(query, {
            'id': id,
            'move_number': move_number,
            'move_notation': move_notation,
            'position_fen': position_fen,
            'eval': eval,
            'eval_change': eval_change,
            'severity': severity
        })

    def connect_blunder_to_game(self, blunder_id, game_id):
        query = """
        MATCH (b:Blunder {id: $blunder_id})
        MATCH (g:Game {id: $game_id})
        MERGE (b)-[:IN]->(g)
        """
        return self.db.query(query, {'blunder_id': blunder_id, 'game_id': game_id})
    
    def connect_player_to_game(self, player_id, game_id, color, rating_at_game):
        query = """
        MATCH (p:Player {id: $player_id})
        MATCH (g:Game {id: $game_id})
        MERGE (p)-[r:PLAYED_IN {color: $color, rating_at_game: $rating_at_game}]->(g)
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
    
    def connect_player_to_blunder(self, player_id, blunder_id, timestamp):
        query = """
        MATCH (p:Player {id: $player_id})
        MATCH (b:Blunder {id: $blunder_id})
        MERGE (p)-[r:MADE_BLUNDER {timestamp: $timestamp}]->(b)
        RETURN r
        """
        return self.db.query(query, {
            'player_id': player_id,
            'blunder_id': blunder_id,
            'timestamp': timestamp
        })
    
    # TODO: Add other entity and relationship methods
