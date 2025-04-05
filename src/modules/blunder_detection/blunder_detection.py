import requests
import math
import io
import chess
import chess.pgn
from chess.engine import SimpleEngine
from src.config import STOCKFISH

class BlunderDetection:
    def __init__(self):
        self.engine = SimpleEngine.popen_uci(STOCKFISH["path"])

    def close(self):
        """Close the engine process when done"""
        if self.engine:
            self.engine.close()
            
    def __del__(self):
        """Destructor to ensure engine is closed"""
        self.close()

    def get_stockfish_evaluation_local(self, fen, depth=STOCKFISH["analysis_depth"]):
        board = chess.Board(fen)
        info = self.engine.analyse(board, chess.engine.Limit(depth=depth))
        
        score = info["score"].relative

        bestmove = None
        if "pv" in info and info["pv"]:
            bestmove = info["pv"][0].uci()
            
        if score.is_mate():
            # This scales mates so that mate in 1 is worth more than mate in 10
            mate_value = 10.0 + 10.0/max(1, abs(score.mate()))
            if score.mate() < 0:
                mate_value = -mate_value
            
            return {
                "eval": mate_value,
                "mate_in": abs(score.mate()),
                "is_mate": True,
                "bestmove": bestmove
            }
        else:
            return {
                "eval": score.score() / 100.0, # Convert to pawns
                "mate_in": None,
                "is_mate": False,
                "bestmove": bestmove
            }

    def get_stockfish_evaluation(self, fen):
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

    def eval_to_win_probability(self, eval_score):
        """Convert engine evaluation to win probability (0-1)"""
        if eval_score is None:
            return 0.5

        win_probability = 1 / (1 + math.exp(-0.00368208 * eval_score * 100))
        return win_probability

    def classify_move(self, current_eval, previous_eval, current_is_mate=False, previous_is_mate=False):
        """
        Classify a move based on evaluation change
        Args:
            current_eval: Current position evaluation (after move)
            previous_eval: Previous position evaluation (before move)
            current_is_mate: Whether current position is a mate
            previous_is_mate: Whether previous position was a mate
        """
        # Special handling for transitions to/from mate positions
        if current_is_mate and not previous_is_mate:
            # If we went from non-mate to mate in our favor, it's a great move
            if current_eval > 0:  # Mate in our favor
                return "Best"
            else:  # Mate against us - serious blunder
                return "Blunder"
                
        elif previous_is_mate and not current_is_mate:
            # If we went from mate in our favor to non-mate, it's a blunder
            if previous_eval > 0:  # Was mate in our favor
                return "Blunder"
            else:  # Was mate against us, now it's not - good save
                return "Best"
        
        # Regular evaluation change based classification
        current_win_prob = self.eval_to_win_probability(current_eval)
        previous_win_prob = self.eval_to_win_probability(previous_eval)
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

    def convert_moves_to_positions(self, moves_string):
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

    def process_game_for_analysis(self, game_moves):
        """Process a game's moves and prepare positions for Stockfish analysis"""
        positions = self.convert_moves_to_positions(game_moves)
        
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

    def analyze_game_for_blunders(self, game_moves):
        """Analyze a game's moves and identify blunders"""
        positions = self.process_game_for_analysis(game_moves)
        
        previous_eval = 0
        
        for i, position in enumerate(positions):
            eval_data = self.get_stockfish_evaluation_local(position["fen"])

            if not eval_data:
                print(f"ERROR: No eval data for position {position['fen']}")
                return None

            current_eval = eval_data["eval"]

            if position["player"] == "Black":
                current_eval = -current_eval

            position["eval"] = current_eval
            position["bestmove"] = eval_data.get("bestmove")
            position["is_mate"] = eval_data.get("is_mate", False)

            if i > 0:
                eval_change = previous_eval - current_eval
                current_is_mate = position.get("is_mate", False)
                previous_is_mate = positions[i-1].get("is_mate", False) if i > 0 else False
                move_class = self.classify_move(current_eval, previous_eval, current_is_mate, previous_is_mate)
                
                position["eval_change"] = eval_change
                position["move_class"] = move_class
            else:
                position["eval_change"] = 0
                position["move_class"] = "Opening"
            
            previous_eval = current_eval

        return positions
