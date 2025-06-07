from typing import Dict, List, Tuple, Any
import numpy as np
from scipy import stats
from src.database.db_manager import Neo4jConnection
import pandas as pd

class Analysis:
    def __init__(self):
        self.db = Neo4jConnection()

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
            results = self.db.query(query)
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
        
        results = self.db.query(query, {'id': player_username})
        
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
        
        results = self.db.query(query)
        
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
            results = self.db.query(query, {'id': player_id})
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
                results = self.db.query(query, {'id': player_id})
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
        results = self.db.query(query, {'id': player_id})
        return results[0]['clustering_coefficient'] if results else 0.0 

    def analyze_opening_network_position(self) -> Dict:
        """
        Analyzes how a player's network position in opening-specific subgraphs
        correlates with their performance in those openings.
        
        Returns:
            Dict containing:
            - Opening-specific network metrics
            - Performance correlations
            - Statistical significance
        """
        query = """
        MATCH (p:Player)-[r1:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)<-[:USES]-(g2:Game)<-[r2:PLAYED_IN]-(p2:Player)
        WHERE p <> p2
        WITH o, p, p2,
             count(DISTINCT g) as games_played,
             sum(CASE
                 WHEN g.winner = r1.color THEN 1
                 WHEN g.winner = 'draw' THEN 0.5
                 ELSE 0
             END) as wins
        WHERE games_played >= 5
        RETURN o.eco_code as opening,
               o.name as opening_name,
               p.username as player,
               toFloat(wins)/games_played as win_rate,
               games_played
        """
        
        results = self.db.query(query)
        
        # Calculate opening-specific network metrics
        opening_metrics = {}
        for result in results:
            opening = result['opening']
            if opening not in opening_metrics:
                opening_metrics[opening] = {
                    'name': result['opening_name'],
                    'players': set(),
                    'win_rates': [],
                    'games_played': []
                }
            
            opening_metrics[opening]['players'].add(result['player'])
            opening_metrics[opening]['win_rates'].append(result['win_rate'])
            opening_metrics[opening]['games_played'].append(result['games_played'])
        
        # Calculate correlations and statistics
        analysis_results = {}
        for opening, metrics in opening_metrics.items():
            if len(metrics['players']) >= 5:  # Only analyze openings with enough players
                win_rates = metrics['win_rates']
                games_played = metrics['games_played']
                
                # Calculate correlation between games played and win rate
                correlation, p_value = stats.pearsonr(games_played, win_rates)
                
                analysis_results[opening] = {
                    'name': metrics['name'],
                    'player_count': len(metrics['players']),
                    'avg_win_rate': np.mean(win_rates),
                    'avg_games_played': np.mean(games_played),
                    'correlation': correlation,
                    'p_value': p_value
                }
        
        return {
            'opening_metrics': analysis_results,
            'total_openings_analyzed': len(analysis_results)
        }

    def analyze_player_network_characteristics(self) -> Dict[str, Any]:
        """
        Analyze how player performance correlates with their network characteristics:
        - Number of unique opponents
        - Average rating difference with opponents
        - Performance against higher/lower rated players
        
        Returns:
            Dict containing:
            - player_stats: DataFrame with player network and performance metrics
            - summary_stats: Dict with overall performance statistics
        """
        query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)<-[:PLAYED_IN]-(opponent:Player)
        WHERE p <> opponent
        WITH p, opponent, g, r,
             opponent.rating_at_game - p.rating_at_game as rating_diff,
             g.winner = r.color as is_win
        WITH p.username as player,
             COUNT(DISTINCT opponent) as unique_opponents,
             AVG(ABS(opponent.rating_at_game - p.rating_at_game)) as avg_rating_diff,
             COUNT(*) as total_games,
             AVG(CASE WHEN is_win THEN 1 ELSE 0 END) as win_rate,
             AVG(CASE 
                 WHEN opponent.rating_at_game > p.rating_at_game AND is_win THEN 1
                 WHEN opponent.rating_at_game > p.rating_at_game THEN 0
                 ELSE NULL 
             END) as win_rate_vs_higher,
             AVG(CASE 
                 WHEN opponent.rating_at_game < p.rating_at_game AND is_win THEN 1
                 WHEN opponent.rating_at_game < p.rating_at_game THEN 0
                 ELSE NULL 
             END) as win_rate_vs_lower
        WHERE total_games >= 10  // Only include players with sufficient games
        RETURN player, unique_opponents, avg_rating_diff, total_games, 
               win_rate, win_rate_vs_higher, win_rate_vs_lower
        ORDER BY total_games DESC
        """
        
        results = self.db.query(query)
        
        # Convert results to DataFrame
        data = []
        for record in results:
            data.append({
                'player': record['player'],
                'unique_opponents': record['unique_opponents'],
                'avg_rating_diff': record['avg_rating_diff'],
                'total_games': record['total_games'],
                'win_rate': record['win_rate'],
                'win_rate_vs_higher': record['win_rate_vs_higher'],
                'win_rate_vs_lower': record['win_rate_vs_lower']
            })
        
        df = pd.DataFrame(data)
        
        # Calculate summary statistics
        summary_stats = {
            'total_players': len(df),
            'avg_unique_opponents': df['unique_opponents'].mean(),
            'avg_rating_diff': df['avg_rating_diff'].mean(),
            'overall_win_rate': df['win_rate'].mean(),
            'win_rate_vs_higher': df['win_rate_vs_higher'].mean(),
            'win_rate_vs_lower': df['win_rate_vs_lower'].mean(),
            'correlation_opponents_winrate': df['unique_opponents'].corr(df['win_rate']),
            'correlation_ratingdiff_winrate': df['avg_rating_diff'].corr(df['win_rate'])
        }
        
        return {
            'player_stats': df,
            'summary_stats': summary_stats
        }

    def analyze_network_position_vs_game_dynamics(self) -> Dict:
        """
        Analyzes how network position affects game dynamics like:
        - Victory status (mate, resign, outoftime)
        - Game length
        - Rating difference impact
        
        Returns:
            Dict containing:
            - Game dynamics metrics by network position
            - Statistical correlations
            - Performance patterns
        """
        query = """
        MATCH (p:Player)-[r1:PLAYED_IN]->(g:Game)<-[r2:PLAYED_IN]-(opp:Player)
        WHERE p <> opp
        WITH p, g, r1, r2,
             abs(toFloat(r1.rating_at_game) - toFloat(r2.rating_at_game)) as rating_diff,
             g.victory_status as status,
             g.turns as turns
        RETURN p.username as player,
               status,
               avg(turns) as avg_game_length,
               avg(rating_diff) as avg_rating_diff,
               count(g) as games_played
        """
        
        results = self.db.query(query)
        
        # Process results
        dynamics_metrics = {
            'mate': {'lengths': [], 'rating_diffs': [], 'games': []},
            'resign': {'lengths': [], 'rating_diffs': [], 'games': []},
            'outoftime': {'lengths': [], 'rating_diffs': [], 'games': []},
            'draw': {'lengths': [], 'rating_diffs': [], 'games': []}
        }
        
        for result in results:
            status = result['status']
            if status in dynamics_metrics:
                dynamics_metrics[status]['lengths'].append(result['avg_game_length'])
                dynamics_metrics[status]['rating_diffs'].append(result['avg_rating_diff'])
                dynamics_metrics[status]['games'].append(result['games_played'])
        
        # Calculate statistics
        analysis = {}
        for status, metrics in dynamics_metrics.items():
            if metrics['games']:  # Only analyze if we have data
                analysis[status] = {
                    'avg_game_length': np.mean(metrics['lengths']),
                    'avg_rating_diff': np.mean(metrics['rating_diffs']),
                    'total_games': sum(metrics['games']),
                    'player_count': len(metrics['games'])
                }
        
        # Calculate correlations between game length and rating difference
        correlations = {}
        for status in analysis:
            if len(dynamics_metrics[status]['lengths']) > 1:
                corr, p_value = stats.pearsonr(
                    dynamics_metrics[status]['lengths'],
                    dynamics_metrics[status]['rating_diffs']
                )
                correlations[status] = {
                    'correlation': corr,
                    'p_value': p_value
                }
        
        analysis['correlations'] = correlations
        
        return analysis 

    def analyze_opening_performance(self) -> Dict[str, Any]:
        """
        Analyze how openings affect player performance:
        - Most common openings
        - Win rates by opening
        - Rating impact of openings
        - Game length by opening
        
        Returns:
            Dict containing:
            - opening_stats: DataFrame with opening performance metrics
            - player_opening_stats: DataFrame with player-specific opening performance
            - summary_stats: Dict with overall opening statistics
        """
        query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH o.eco_code as opening_code,
             o.name as opening_name,
             COUNT(*) as games_played,
             AVG(CASE WHEN g.winner = r.color THEN 1 ELSE 0 END) as win_rate,
             AVG(g.turns) as avg_game_length,
             AVG(ABS(p.rating_at_game - 
                 [(p)-[:PLAYED_IN]->(g)<-[:PLAYED_IN]-(opponent:Player) | opponent.rating_at_game][0])) as avg_rating_diff
        WHERE games_played >= 10  // Only include openings with sufficient games
        RETURN opening_code, opening_name, games_played, win_rate, avg_game_length, avg_rating_diff
        ORDER BY games_played DESC
        """
        
        results = self.db.query(query)
        
        # Convert results to DataFrame
        data = []
        for record in results:
            data.append({
                'opening_code': record['opening_code'],
                'opening_name': record['opening_name'],
                'games_played': record['games_played'],
                'win_rate': record['win_rate'],
                'avg_game_length': record['avg_game_length'],
                'avg_rating_diff': record['avg_rating_diff']
            })
        
        opening_stats = pd.DataFrame(data)
        
        # Get player-specific opening performance
        player_query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH p.username as player,
             o.eco_code as opening_code,
             o.name as opening_name,
             COUNT(*) as games_played,
             AVG(CASE WHEN g.winner = r.color THEN 1 ELSE 0 END) as win_rate
        WHERE games_played >= 5  // Only include openings where player has sufficient games
        RETURN player, opening_code, opening_name, games_played, win_rate
        ORDER BY player, games_played DESC
        """
        
        player_results = self.db.query(player_query)
        
        player_data = []
        for record in player_results:
            player_data.append({
                'player': record['player'],
                'opening_code': record['opening_code'],
                'opening_name': record['opening_name'],
                'games_played': record['games_played'],
                'win_rate': record['win_rate']
            })
        
        player_opening_stats = pd.DataFrame(player_data)
        
        # Calculate summary statistics
        summary_stats = {
            'total_openings': len(opening_stats),
            'total_games': opening_stats['games_played'].sum(),
            'avg_games_per_opening': opening_stats['games_played'].mean(),
            'most_common_opening': opening_stats.iloc[0]['opening_name'],
            'highest_winrate_opening': opening_stats.loc[opening_stats['win_rate'].idxmax()]['opening_name'],
            'shortest_avg_game': opening_stats.loc[opening_stats['avg_game_length'].idxmin()]['opening_name'],
            'longest_avg_game': opening_stats.loc[opening_stats['avg_game_length'].idxmax()]['opening_name']
        }
        
        return {
            'opening_stats': opening_stats,
            'player_opening_stats': player_opening_stats,
            'summary_stats': summary_stats
        } 
