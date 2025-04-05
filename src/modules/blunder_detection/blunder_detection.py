import requests
import math
import io
import chess
import chess.pgn

class BlunderDetection:
    @staticmethod
    def get_stockfish_evaluation(fen):
        """Get position evaluation from Stockfish online API"""
        base_url = "https://stockfish.online/api/s/v2.php"
        params = {
            "fen": fen,
            "depth": 15
        }
    
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"API error: Status code {response.status_code}")
                return None
                
            data = response.json()

            if data.get("success"):
                return {
                    "eval": data.get("evaluation", 0),
                    "mate_in": data.get("mate"),
                    "bestmove": data.get("bestmove", "").split()[1]
                }
            else:
                print(f"API error: {data}")
                return None
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except (ValueError, KeyError, IndexError) as e:
            print(f"Data parsing error: {e}")
            return None

    @staticmethod
    def eval_to_win_probability(eval_score):
        """Convert engine evaluation to win probability (0-1)"""
        if eval_score is None:
            return 0.5
        
        # Handle mate scores
        if isinstance(eval_score, str) and 'mate' in eval_score:
            mate_in = int(eval_score.split('mate')[1].strip())
            return 1.0 if mate_in > 0 else 0.0
        
        # Convert centipawns to win probability using sigmoid function
        # Similar to what chess.com uses
        win_probability = 1 / (1 + math.exp(-0.00368208 * eval_score * 100))
        return win_probability

    @staticmethod
    def classify_move(current_eval, previous_eval):
        current_win_prob = BlunderDetection.eval_to_win_probability(current_eval)
        previous_win_prob = BlunderDetection.eval_to_win_probability(previous_eval)
        win_prob_change = previous_win_prob - current_win_prob
        
        # Chess.com classification
        if win_prob_change <= 0:
            return "Best"
        elif 0 < win_prob_change <= 0.02:
            return "Excellent"
        elif 0.02 < win_prob_change <= 0.05:
            return "Good"
        elif 0.05 < win_prob_change <= 0.10:
            return "Inaccuracy"
        elif 0.10 < win_prob_change <= 0.20:
            return "Mistake"
        else:  # win_prob_change > 0.20
            return "Blunder"

    @staticmethod
    def convert_moves_to_positions(moves_string):
        """Convert a string of moves to a list of FEN positions after each move"""
        board = chess.Board()
        moves_list = moves_string.split()
        positions = []
        
        # Starting position
        positions.append(board.fen())
        
        # Apply each move and record the resulting position
        for move_str in moves_list:
            try:
                # Parse the move in algebraic notation
                move = board.parse_san(move_str)
                # Apply the move to the board
                board.push(move)
                # Record the position after the move
                positions.append(board.fen())
            except ValueError as e:
                print(f"Error parsing move: {move_str}")
                print(e)
                break
        
        return positions

    @staticmethod
    def process_game_for_analysis(game_moves):
        """Process a game's moves and prepare positions for Stockfish analysis"""
        positions = BlunderDetection.convert_moves_to_positions(game_moves)
        
        # For each position, get the evaluation
        results = []
        for i, fen in enumerate(positions[1:], 1):  # Skip initial position
            # Determine whose turn it was
            is_white_turn = i % 2 == 1
            player = "White" if is_white_turn else "Black"
            move_number = (i + 1) // 2  # Calculate move number
            
            results.append({
                "move_number": move_number,
                "move_notation": game_moves.split()[i-1],
                "player": player,
                "fen": fen,
                "move_played": game_moves.split()[i-1]  # The move that led to this position
            })
        
        return results

    @staticmethod
    def analyze_game_for_blunders(game_moves):
        """Analyze a game's moves and identify blunders"""
        positions = BlunderDetection.process_game_for_analysis(game_moves)
        
        previous_eval = 0
        
        for i, position in enumerate(positions):
            eval_data = BlunderDetection.get_stockfish_evaluation(position["fen"])

            if not eval_data:
                print(f"ERROR: No eval data for position {position['fen']}")
                return {"error": "No eval data for position"}

            current_eval = eval_data["eval"]
            if eval_data["mate_in"] is not None:
                try:
                    mate_in = int(eval_data["mate_in"])
                    current_eval = 100 if mate_in > 0 else -100
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert mate value '{eval_data['mate_in']}' to integer.")
                    current_eval = 0

            if position["player"] == "Black":
                current_eval = -current_eval
             
            position["eval"] = current_eval
            position["bestmove"] = eval_data["bestmove"]

            if i > 0:
                eval_change = previous_eval - current_eval
                move_class = BlunderDetection.classify_move(current_eval, previous_eval)
                
                position["eval_change"] = eval_change
                position["move_class"] = move_class
            else:
                position["eval_change"] = 0
                position["move_class"] = "Opening"
            
            previous_eval = current_eval

        return positions
