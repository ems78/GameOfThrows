from typing import Dict, List, Tuple
import numpy as np
from scipy import stats
from src.modules.database.queries import GraphQueries
import pandas as pd

class PlayerNetworkAnalysis:
    def __init__(self):
        self.queries = GraphQueries()

    def analyze_rating_progression_by_opponent_rating(self) -> Dict:
        """
        Analyze how players' ratings change based on their opponents' ratings.
        Returns correlation between rating difference and rating change.
        """
        try:
            print("Starting rating progression analysis...")
            query = """
            MATCH (p:Player)-[r1:PLAYED_IN]->(g:Game)<-[r2:PLAYED_IN]-(opp:Player)
            WHERE p <> opp
            WITH p, g, r1, r2, opp,
                 r1.rating_at_game as player_rating,
                 r2.rating_at_game as opponent_rating,
                 g.winner as winner,
                 r1.color as player_color
            WITH p, g, player_rating, opponent_rating, winner, player_color,
                 CASE 
                     WHEN (player_color = 'white' AND winner = 'white') OR 
                          (player_color = 'black' AND winner = 'black') THEN 1
                     WHEN winner = 'draw' THEN 0.5
                     ELSE 0
                 END as actual_result,
                 // Calculate expected result using Elo formula
                 1.0 / (1.0 + 10.0 ^ ((opponent_rating - player_rating) / 400.0)) as expected_result
            WITH p, g, player_rating, opponent_rating, actual_result, expected_result,
                 // Use K=16 for established players
                 16 * (actual_result - expected_result) as rating_change,
                 opponent_rating - player_rating as rating_diff
            RETURN p.username as player,
                   g.id as game_id,
                   player_rating,
                   opponent_rating,
                   rating_diff,
                   rating_change
            ORDER BY g.created_at
            """
            
            print("Executing Neo4j query...")
            results = self.queries.db.query(query)
            print(f"Query returned {len(results)} records")
            
            if not results:
                print("No data returned from query")
                return {
                    'correlation': None,
                    'p_value': None,
                    'sample_size': 0,
                    'raw_data': []
                }
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(record) for record in results])
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"Sample data:\n{df.head()}")
            
            # Calculate correlation
            correlation, p_value = stats.pearsonr(df['rating_diff'], df['rating_change'])
            print(f"Correlation: {correlation}, p-value: {p_value}")
            
            return {
                'correlation': correlation,
                'p_value': p_value,
                'sample_size': len(df),
                'raw_data': df.to_dict('records')
            }
        except Exception as e:
            print(f"Error in analyze_rating_progression_by_opponent_rating: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def predict_rating_progression(self, player_username: str) -> Dict:
        """
        Predicts a player's rating progression based on their network position
        and game history.
        
        Args:
            player_username: Username/ID of the player to analyze
            
        Returns:
            Dict containing:
            - predicted rating progression
            - confidence interval
            - factors contributing to the prediction
        """
        query = """
        MATCH (p:Player {id: $id})-[r:PLAYED_IN]->(g:Game)
        WITH p, g, r,
             datetime(g.created_at) as game_time
        ORDER BY game_time
        WITH p,
             collect({
                 rating: toFloat(r.rating_at_game),
                 time: game_time,
                 opponent_rating: CASE
                     WHEN r.color = 'white' THEN toFloat(head([(p2)-[r2:PLAYED_IN]->(g) | r2.rating_at_game]))
                     ELSE toFloat(head([(p2)-[r2:PLAYED_IN]->(g) | r2.rating_at_game]))
                 END,
                 result: CASE
                     WHEN g.winner = r.color THEN 1
                     WHEN g.winner = 'draw' THEN 0.5
                     ELSE 0
                 END
             }) as games
        WHERE size(games) >= 5
        RETURN p.id as player_id,
               p.username as username,
               [g in games | g.rating] as ratings,
               [g in games | g.time] as times,
               [g in games | g.opponent_rating] as opponent_ratings,
               [g in games | g.result] as results
        """
        
        results = self.queries.db.query(query, {'id': player_username})
        
        if not results:
            return {'error': 'Player not found or insufficient games'}
            
        data = results[0]
        
        if len(data['ratings']) < 5:
            return {'error': 'Insufficient games for analysis'}
        
        # Calculate network metrics
        centrality = self._calculate_centrality(player_username)
        
        return {
            'player_id': data['player_id'],
            'username': data.get('username', player_username),  # Use ID if username is null
            'ratings': data['ratings'],
            'times': data['times'],
            'opponent_ratings': data['opponent_ratings'],
            'results': data['results'],
            'centrality': centrality
        }

    def analyze_network_position_vs_winrate(self) -> Dict:
        """
        Analyzes how a player's network position (centrality, clustering coefficient)
        correlates with their win rate against similarly rated opponents.
        
        Returns:
            Dict containing:
            - correlation between network metrics and win rates
            - statistical significance
            - detailed analysis by rating ranges
        """
        query = """
        MATCH (p:Player)-[r1:PLAYED_IN]->(g:Game)<-[r2:PLAYED_IN]-(opp:Player)
        WHERE p <> opp
        WITH p, opp, g, r1, r2,
             abs(toFloat(r1.rating_at_game) - toFloat(r2.rating_at_game)) as rating_diff
        WHERE rating_diff <= 100  // Only consider games against similarly rated opponents
        WITH p,
             count(g) as total_games,
             sum(CASE
                 WHEN g.winner = r1.color THEN 1
                 WHEN g.winner = 'draw' THEN 0.5
                 ELSE 0
             END) as wins
        WHERE total_games >= 10
        RETURN p.id as player_id,
               p.username as username,
               toFloat(p.rating) as rating,
               wins/total_games as win_rate,
               total_games
        """
        
        results = self.queries.db.query(query)
        
        # Calculate network metrics for each player
        player_metrics = []
        for result in results:
            player_id = result['player_id']
            centrality = self._calculate_centrality(player_id)
            clustering = self._calculate_clustering(player_id)
            
            player_metrics.append({
                'player_id': player_id,
                'username': result.get('username', player_id),  # Use ID if username is null
                'rating': result['rating'],
                'win_rate': result['win_rate'],
                'centrality': centrality,
                'clustering': clustering
            })
        
        # Calculate correlations
        win_rates = [p['win_rate'] for p in player_metrics]
        centralities = [p['centrality'] for p in player_metrics]
        clusterings = [p['clustering'] for p in player_metrics]
        
        centrality_corr, centrality_p = stats.pearsonr(win_rates, centralities)
        clustering_corr, clustering_p = stats.pearsonr(win_rates, clusterings)
        
        return {
            'centrality_correlation': {
                'correlation': centrality_corr,
                'p_value': centrality_p
            },
            'clustering_correlation': {
                'correlation': clustering_corr,
                'p_value': clustering_p
            },
            'sample_size': len(player_metrics),
            'raw_data': player_metrics
        }

    def _calculate_centrality(self, player_id: str) -> float:
        """Calculate betweenness centrality for a player."""
        # First try using GDS library
        try:
            query = """
            CALL gds.betweenness.stream({
                nodeProjection: 'Player',
                relationshipProjection: {
                    PLAYED_IN: {
                        type: 'PLAYED_IN',
                        orientation: 'UNDIRECTED'
                    }
                }
            })
            YIELD nodeId, score
            WHERE gds.util.asNode(nodeId).id = $id
            RETURN score
            """
            results = self.queries.db.query(query, {'id': player_id})
            return results[0]['score'] if results else 0.0
        except Exception as e:
            if "ProcedureNotFound" in str(e):
                # Fallback to a simpler degree centrality calculation
                query = """
                MATCH (p:Player {id: $id})-[r:PLAYED_IN]->(g:Game)
                WITH p, count(DISTINCT g) as games_played
                MATCH (p2:Player)-[r2:PLAYED_IN]->(g2:Game)
                WITH p, games_played, count(DISTINCT p2) as total_players,
                     count(DISTINCT g2) as total_games
                RETURN toFloat(games_played) / toFloat(total_games) as centrality
                """
                results = self.queries.db.query(query, {'id': player_id})
                return results[0]['centrality'] if results else 0.0
            else:
                # Re-raise if it's a different error
                raise

    def _calculate_clustering(self, player_id: str) -> float:
        """Calculate local clustering coefficient for a player."""
        query = """
        MATCH (p:Player {id: $id})-[:PLAYED_IN]->(g1:Game)<-[:PLAYED_IN]-(opp1:Player)
        MATCH (p)-[:PLAYED_IN]->(g2:Game)<-[:PLAYED_IN]-(opp2:Player)
        WHERE opp1 <> opp2
        MATCH (opp1)-[:PLAYED_IN]->(g3:Game)<-[:PLAYED_IN]-(opp2)
        WITH p, count(DISTINCT g3) as triangles,
             count(DISTINCT opp1) * (count(DISTINCT opp1) - 1) / 2 as possible_triangles
        RETURN CASE
            WHEN possible_triangles > 0 THEN triangles / possible_triangles
            ELSE 0
        END as clustering_coefficient
        """
        results = self.queries.db.query(query, {'id': player_id})
        return results[0]['clustering_coefficient'] if results else 0.0 
