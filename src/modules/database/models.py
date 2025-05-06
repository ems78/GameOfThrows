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
    
    def create_blunder(self, id, move_number, move_notation, best_move, position_fen, eval, eval_change, is_mate, severity=None):
        query = """
        MERGE (b:Blunder {id: $id})
        ON CREATE SET 
            b.move_number = $move_number,
            b.move_notation = $move_notation,
            b.best_move = $best_move,
            b.position_fen = $position_fen,
            b.eval = $eval,
            b.eval_change = $eval_change,
            b.is_mate = $is_mate,
            b.severity = $severity
        RETURN b
        """
        return self.db.query(query, {
            'id': id,
            'move_number': move_number,
            'move_notation': move_notation,
            'best_move': best_move,
            'position_fen': position_fen,
            'eval': eval,
            'eval_change': eval_change,
            'is_mate': is_mate,
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
    
    def create_weighted_blunder_graph(self):
        """
        Creates a weighted graph analysis that combines player ratings with blunder evaluation changes.
        This method:
        1. Creates a weighted relationship between players based on their blunders
        2. The weight is calculated as a normalized combination of:
           - The player's rating (normalized to 0-1 range)
           - The absolute evaluation change of the blunder (normalized to 0-1 range)
        3. Returns the graph data for further analysis
        """
        # First, create a temporary graph with weighted relationships
        query = """
        // Find all players who made blunders
        MATCH (p1:Player)-[:MADE_BLUNDER]->(b:Blunder)
        
        // Calculate player's average blunder severity
        WITH p1, avg(abs(toFloat(b.eval_change))) as avg_eval_change1, max(abs(toFloat(b.eval_change))) as max_eval_change1
        
        // Find other players who made blunders
        MATCH (p2:Player)-[:MADE_BLUNDER]->(b2:Blunder)
        WHERE p1 <> p2
        
        // Calculate second player's average blunder severity
        WITH p1, p2, avg_eval_change1, max_eval_change1, 
             avg(abs(toFloat(b2.eval_change))) as avg_eval_change2, 
             max(abs(toFloat(b2.eval_change))) as max_eval_change2
        
        // Calculate normalized weights
        WITH p1, p2,
             // Normalize player ratings (assuming typical range 1000-3000)
             (toFloat(p1.rating) - 1000) / 2000 as norm_rating1,
             (toFloat(p2.rating) - 1000) / 2000 as norm_rating2,
             // Normalize evaluation changes
             CASE WHEN max_eval_change1 > 0 
                  THEN avg_eval_change1 / max_eval_change1 
                  ELSE 0 END as norm_eval_change1,
             CASE WHEN max_eval_change2 > 0 
                  THEN avg_eval_change2 / max_eval_change2 
                  ELSE 0 END as norm_eval_change2,
             avg_eval_change1,
             avg_eval_change2
        
        // Create weighted relationship between players
        MERGE (p1)-[r:BLUNDER_SIMILARITY {
            weight: (norm_rating1 + norm_rating2) / 2 * (1 - (norm_eval_change1 + norm_eval_change2) / 2),
            rating_diff: abs(toFloat(p1.rating) - toFloat(p2.rating)),
            avg_eval_change1: avg_eval_change1,
            avg_eval_change2: avg_eval_change2
        }]->(p2)
        
        RETURN p1.id as player1_id, p2.id as player2_id, 
               p1.username as player1_username, p2.username as player2_username,
               p1.rating as player1_rating, p2.rating as player2_rating,
               r.weight as weight, r.rating_diff as rating_diff, 
               r.avg_eval_change1 as avg_eval_change1, r.avg_eval_change2 as avg_eval_change2
        ORDER BY r.weight DESC
        LIMIT 100
        """
        return self.db.query(query)
    
    def get_player_blunder_stats(self):
        """
        Returns statistics about player blunders including:
        - Average evaluation change
        - Maximum evaluation change
        - Number of blunders
        - Rating at time of blunders
        """
        query = """
        MATCH (p:Player)-[r:MADE_BLUNDER]->(b:Blunder)
        WITH p, b
        RETURN 
            p.username,
            p.rating,
            count(b) as blunder_count,
            avg(abs(toFloat(b.eval_change))) as avg_eval_change,
            max(abs(toFloat(b.eval_change))) as max_eval_change,
            min(abs(toFloat(b.eval_change))) as min_eval_change
        ORDER BY avg_eval_change DESC
        """
        return self.db.query(query)
    
    # TODO: Add other entity and relationship methods
