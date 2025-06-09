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
        WHERE games_played >= 3 
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
            if len(metrics['players']) >= 3:  # Reduced from 5 to 3
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

    def analyze_network_position_vs_winrate(self) -> Dict:
        """
        Analyzes how a player's network position (centrality, clustering coefficient)
        correlates with their win rate against similarly rated opponents.
        
        Returns:
            Dict containing:
            - correlation between network metrics and win rates
            - statistical significance
            - detailed analysis by rating ranges
            - opening repertoire diversity
            - game length patterns
        """
        print("\n=== Network Position vs Win Rate Analysis ===")
        print("Analyzing how player network position affects performance...")
        
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
             END) as wins,
             avg(g.turns) as avg_game_length,
             count(DISTINCT g.increment_code) as time_control_variety
        WHERE total_games >= 10
        WITH p, total_games, wins, avg_game_length, time_control_variety,
             toFloat(wins)/toFloat(total_games) as win_rate
        MATCH (p)-[:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH p, total_games, wins, avg_game_length, time_control_variety, win_rate,
             count(DISTINCT o.eco_code) as opening_variety,
             collect(DISTINCT o.eco_code) as openings_played
        RETURN p.id as player_id,
               p.username as username,
               toFloat(p.rating) as rating,
               win_rate,
               total_games,
               wins,
               avg_game_length,
               time_control_variety,
               opening_variety,
               openings_played
        """
        
        results = self.db.query(query)
        print(f"\nAnalyzed {len(results)} players with sufficient game history")
        
        # Calculate network metrics for each player
        player_metrics = []
        for result in results:
            player_id = result['player_id']
            centrality = self._calculate_centrality(player_id)
            clustering = self._calculate_clustering(player_id)
            
            # Calculate opening repertoire diversity
            openings = result['openings_played']
            opening_diversity = len(set(openings)) / len(openings) if openings else 0
            
            player_metrics.append({
                'player_id': player_id,
                'username': result.get('username', player_id),
                'rating': result['rating'],
                'win_rate': result['win_rate'],
                'centrality': centrality,
                'clustering': clustering,
                'avg_game_length': result['avg_game_length'],
                'time_control_variety': result['time_control_variety'],
                'opening_variety': result['opening_variety'],
                'opening_diversity': opening_diversity
            })
        
        # Calculate correlations
        win_rates = [p['win_rate'] for p in player_metrics]
        centralities = [p['centrality'] for p in player_metrics]
        clusterings = [p['clustering'] for p in player_metrics]
        opening_diversities = [p['opening_diversity'] for p in player_metrics]
        
        # Print key metrics
        print("\n=== Key Performance Metrics ===")
        print(f"Average Win Rate: {np.mean(win_rates):.3f}")
        print(f"Win Rate Std Dev: {np.std(win_rates):.3f}")
        print(f"Average Centrality: {np.mean(centralities):.3f}")
        print(f"Average Clustering: {np.mean(clusterings):.3f}")
        print(f"Average Opening Diversity: {np.mean(opening_diversities):.3f}")
        
        # Helper function to check if array is constant
        def is_constant(arr):
            return len(set(arr)) <= 1
        
        # Calculate correlations only if arrays are not constant
        centrality_corr, centrality_p = (0, 1) if is_constant(centralities) else stats.pearsonr(win_rates, centralities)
        clustering_corr, clustering_p = (0, 1) if is_constant(clusterings) else stats.pearsonr(win_rates, clusterings)
        diversity_corr, diversity_p = (0, 1) if is_constant(opening_diversities) else stats.pearsonr(win_rates, opening_diversities)
        
        print("\n=== Correlation Analysis ===")
        print(f"Centrality vs Win Rate: {centrality_corr:.3f} (p-value: {centrality_p:.3f})")
        print(f"Clustering vs Win Rate: {clustering_corr:.3f} (p-value: {clustering_p:.3f})")
        print(f"Opening Diversity vs Win Rate: {diversity_corr:.3f} (p-value: {diversity_p:.3f})")
        
        # Calculate rating range statistics
        rating_ranges = [(0, 1200), (1200, 1400), (1400, 1600), (1600, 1800), (1800, 2000), (2000, float('inf'))]
        range_stats = {}
        
        print("\n=== Performance by Rating Range ===")
        for low, high in rating_ranges:
            range_players = [p for p in player_metrics if low <= p['rating'] < high]
            if range_players:
                range_stats[f"{low}-{high}"] = {
                    'count': len(range_players),
                    'avg_win_rate': np.mean([p['win_rate'] for p in range_players]),
                    'avg_centrality': np.mean([p['centrality'] for p in range_players]),
                    'avg_clustering': np.mean([p['clustering'] for p in range_players]),
                    'avg_opening_diversity': np.mean([p['opening_diversity'] for p in range_players])
                }
                print(f"\nRating Range {low}-{high}:")
                print(f"  Players: {len(range_players)}")
                print(f"  Avg Win Rate: {range_stats[f'{low}-{high}']['avg_win_rate']:.3f}")
                print(f"  Avg Centrality: {range_stats[f'{low}-{high}']['avg_centrality']:.3f}")
                print(f"  Avg Clustering: {range_stats[f'{low}-{high}']['avg_clustering']:.3f}")
                print(f"  Avg Opening Diversity: {range_stats[f'{low}-{high}']['avg_opening_diversity']:.3f}")
        
        return {
            'centrality_correlation': {
                'correlation': centrality_corr,
                'p_value': centrality_p
            },
            'clustering_correlation': {
                'correlation': clustering_corr,
                'p_value': clustering_p
            },
            'opening_diversity_correlation': {
                'correlation': diversity_corr,
                'p_value': diversity_p
            },
            'rating_range_stats': range_stats,
            'sample_size': len(player_metrics),
            'raw_data': player_metrics
        }

    def analyze_opening_performance(self) -> Dict[str, Any]:
        """
        Analyze how openings affect player performance:
        - Performance metrics by rating level
        - Opening transition patterns
        - Win rates and game characteristics by opening
        
        Returns:
            Dict containing:
            - opening_stats: DataFrame with opening performance metrics
            - rating_level_stats: DataFrame with performance by rating level
            - transition_stats: DataFrame with opening transition patterns
            - summary_stats: Dict with overall opening statistics
        """
        print("\n=== Opening Performance Analysis ===")
        print("Analyzing opening performance across different rating levels...")
        
        # Basic opening statistics
        query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH o.eco_code as opening_code,
             o.name as opening_name,
             r.color as color,
             COUNT(*) as games_played,
             AVG(CASE WHEN g.winner = r.color THEN 1 ELSE 0 END) as win_rate,
             AVG(g.turns) as avg_game_length,
             AVG(ABS(p.rating_at_game - 
                 [(p)-[:PLAYED_IN]->(g)<-[:PLAYED_IN]-(opponent:Player) | opponent.rating_at_game][0])) as avg_rating_diff
        WHERE games_played >= 10
        RETURN opening_code, opening_name, color, games_played, win_rate, avg_game_length, avg_rating_diff
        ORDER BY opening_code, color
        """
        
        results = self.db.query(query)
        print(f"\nAnalyzed {len(results)} opening-color combinations with sufficient games")
        
        # Convert results to DataFrame
        data = []
        for record in results:
            data.append({
                'opening_code': record['opening_code'],
                'opening_name': record['opening_name'],
                'color': record['color'],
                'games_played': record['games_played'],
                'win_rate': record['win_rate'],
                'avg_game_length': record['avg_game_length'],
                'avg_rating_diff': record['avg_rating_diff']
            })
        
        opening_stats = pd.DataFrame(data)
        
        # Print top performing openings
        print("\n=== Top Performing Openings ===")
        for color in ['white', 'black']:
            color_stats = opening_stats[opening_stats['color'] == color]
            top_openings = color_stats.nlargest(5, 'win_rate')
            print(f"\nTop 5 {color} openings by win rate:")
            for _, row in top_openings.iterrows():
                print(f"  {row['opening_code']} ({row['opening_name']}):")
                print(f"    Win Rate: {row['win_rate']:.3f}")
                print(f"    Games Played: {row['games_played']}")
                print(f"    Avg Game Length: {row['avg_game_length']:.1f} moves")
        
        # Performance by rating level
        rating_query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH o.eco_code as opening_code,
             o.name as opening_name,
             r.color as color,
             CASE 
                 WHEN p.rating_at_game < 1500 THEN 'Beginner'
                 WHEN p.rating_at_game < 2000 THEN 'Intermediate'
                 ELSE 'Advanced'
             END as rating_level,
             COUNT(*) as games_played,
             AVG(CASE WHEN g.winner = r.color THEN 1 ELSE 0 END) as win_rate
        WHERE games_played >= 5
        RETURN opening_code, opening_name, color, rating_level, games_played, win_rate
        ORDER BY opening_code, color, rating_level
        """
        
        rating_results = self.db.query(rating_query)
        print(f"\nAnalyzed {len(rating_results)} opening-rating level combinations")
        
        # Convert rating results to DataFrame
        rating_data = []
        for record in rating_results:
            rating_data.append({
                'opening_code': record['opening_code'],
                'opening_name': record['opening_name'],
                'color': record['color'],
                'rating_level': record['rating_level'],
                'games_played': record['games_played'],
                'win_rate': record['win_rate']
            })
        
        rating_level_stats = pd.DataFrame(rating_data)
        
        # Print performance by rating level
        print("\n=== Performance by Rating Level ===")
        for level in ['Beginner', 'Intermediate', 'Advanced']:
            level_stats = rating_level_stats[rating_level_stats['rating_level'] == level]
            if not level_stats.empty:
                print(f"\n{level} Players:")
                print(f"  Total Games: {level_stats['games_played'].sum()}")
                print(f"  Average Win Rate: {level_stats['win_rate'].mean():.3f}")
                most_common = level_stats.groupby('opening_code')['games_played'].sum().idxmax()
                most_common_name = level_stats[level_stats['opening_code'] == most_common]['opening_name'].iloc[0]
                print(f"  Most Common Opening: {most_common} ({most_common_name})")
        
        # Opening transition patterns
        transition_query = """
        MATCH (p:Player)-[:PLAYED_IN]->(g1:Game)-[:USES]->(o1:Opening)
        MATCH (p)-[:PLAYED_IN]->(g2:Game)-[:USES]->(o2:Opening)
        WHERE g1.created_at < g2.created_at
        AND g2.created_at - g1.created_at < 86400000  // Within 24 hours
        WITH o1.eco_code as from_opening,
             o2.eco_code as to_opening,
             COUNT(*) as transition_count
        WHERE transition_count >= 5
        RETURN from_opening, to_opening, transition_count
        ORDER BY transition_count DESC
        """
        
        transition_results = self.db.query(transition_query)
        print(f"\nAnalyzed {len(transition_results)} opening transitions")
        
        # Convert transition results to DataFrame
        transition_data = []
        for record in transition_results:
            transition_data.append({
                'from_opening': record['from_opening'],
                'to_opening': record['to_opening'],
                'transition_count': record['transition_count']
            })
        
        transition_stats = pd.DataFrame(transition_data)
        
        # Print common transitions
        print("\n=== Common Opening Transitions ===")
        top_transitions = sorted(transition_results, key=lambda x: x['transition_count'], reverse=True)[:5]
        for transition in top_transitions:
            print(f"  {transition['from_opening']} → {transition['to_opening']}: {transition['transition_count']} times")
        
        # Calculate summary statistics
        summary_stats = {
            'total_openings': len(opening_stats) // 2,  # Divide by 2 because we have separate white/black stats
            'total_games': opening_stats['games_played'].sum(),
            'avg_games_per_opening': opening_stats['games_played'].mean(),
            'most_common_opening': opening_stats.iloc[0]['opening_name'],
            'highest_winrate_opening': opening_stats.loc[opening_stats['win_rate'].idxmax()]['opening_name'],
            'shortest_avg_game': opening_stats.loc[opening_stats['avg_game_length'].idxmin()]['opening_name'],
            'longest_avg_game': opening_stats.loc[opening_stats['avg_game_length'].idxmax()]['opening_name']
        }
        
        print("\n=== Summary Statistics ===")
        print(f"Total Unique Openings: {summary_stats['total_openings']}")
        print(f"Total Games Analyzed: {summary_stats['total_games']}")
        print(f"Average Games per Opening: {summary_stats['avg_games_per_opening']:.1f}")
        print(f"Most Common Opening: {summary_stats['most_common_opening']}")
        print(f"Highest Win Rate Opening: {summary_stats['highest_winrate_opening']}")
        print(f"Shortest Average Game: {summary_stats['shortest_avg_game']}")
        print(f"Longest Average Game: {summary_stats['longest_avg_game']}")
        
        return {
            'opening_stats': opening_stats,
            'rating_level_stats': rating_level_stats,
            'transition_stats': transition_stats,
            'summary_stats': summary_stats
        }

    def analyze_gateway_openings(self) -> Dict[str, Any]:
        """
        Analyzes openings to identify gateway openings that lead to specific types of positions
        or outcomes. A gateway opening is one that:
        1. Frequently transitions to other openings
        2. Has high betweenness centrality in the opening network
        3. Consistently leads to specific types of positions
        
        Returns:
            Dict containing:
            - gateway_openings: DataFrame with gateway opening metrics
            - transition_network: Dict with opening transition statistics
            - position_types: Dict mapping openings to position characteristics
        """
        # First, analyze opening transitions
        transition_query = """
        MATCH (g1:Game)-[:USES]->(o1:Opening)
        MATCH (g2:Game)-[:USES]->(o2:Opening)
        WHERE g1.created_at < g2.created_at
        AND g1.winner IS NOT NULL
        WITH o1, o2, 
             count(*) as transition_count,
             sum(CASE WHEN g1.winner = 'white' THEN 1 ELSE 0 END) as white_wins,
             sum(CASE WHEN g1.winner = 'black' THEN 1 ELSE 0 END) as black_wins,
             sum(CASE WHEN g1.winner = 'draw' THEN 1 ELSE 0 END) as draws,
             avg(g1.turns) as avg_game_length
        WHERE transition_count >= 5  // Only consider significant transitions
        RETURN o1.eco_code as from_opening,
               o1.name as from_name,
               o2.eco_code as to_opening,
               o2.name as to_name,
               transition_count,
               white_wins,
               black_wins,
               draws,
               toFloat(white_wins)/transition_count as white_win_rate,
               toFloat(black_wins)/transition_count as black_win_rate,
               toFloat(draws)/transition_count as draw_rate,
               avg_game_length
        ORDER BY transition_count DESC
        """
        
        transition_results = self.db.query(transition_query)
        
        # Convert transition results to DataFrame
        transition_data = []
        for record in transition_results:
            transition_data.append({
                'from_opening': record['from_opening'],
                'from_name': record['from_name'],
                'to_opening': record['to_opening'],
                'to_name': record['to_name'],
                'transition_count': record['transition_count'],
                'white_wins': record['white_wins'],
                'black_wins': record['black_wins'],
                'draws': record['draws'],
                'white_win_rate': record['white_win_rate'],
                'black_win_rate': record['black_win_rate'],
                'draw_rate': record['draw_rate'],
                'avg_game_length': record['avg_game_length']
            })
        
        transition_df = pd.DataFrame(transition_data)
        
        # Calculate gateway metrics for each opening
        gateway_query = """
        MATCH (o:Opening)
        WITH o
        OPTIONAL MATCH (g:Game)-[:USES]->(o)
        WITH o, count(g) as total_games
        OPTIONAL MATCH (g:Game)-[:USES]->(o)
        WHERE g.winner IS NOT NULL
        WITH o, total_games,
             count(g) as games_with_result,
             sum(CASE WHEN g.winner = 'white' THEN 1 ELSE 0 END) as white_wins,
             sum(CASE WHEN g.winner = 'black' THEN 1 ELSE 0 END) as black_wins,
             sum(CASE WHEN g.winner = 'draw' THEN 1 ELSE 0 END) as draws,
             avg(g.turns) as avg_game_length
        WHERE total_games >= 10  // Only consider openings with sufficient games
        RETURN o.eco_code as opening_code,
               o.name as opening_name,
               total_games,
               games_with_result,
               white_wins,
               black_wins,
               draws,
               toFloat(white_wins)/games_with_result as white_win_rate,
               toFloat(black_wins)/games_with_result as black_win_rate,
               toFloat(draws)/games_with_result as draw_rate,
               avg_game_length
        ORDER BY total_games DESC
        """
        
        gateway_results = self.db.query(gateway_query)
        
        # Convert gateway results to DataFrame
        gateway_data = []
        for record in gateway_results:
            gateway_data.append({
                'opening_code': record['opening_code'],
                'opening_name': record['opening_name'],
                'total_games': record['total_games'],
                'games_with_result': record['games_with_result'],
                'white_wins': record['white_wins'],
                'black_wins': record['black_wins'],
                'draws': record['draws'],
                'white_win_rate': record['white_win_rate'],
                'black_win_rate': record['black_win_rate'],
                'draw_rate': record['draw_rate'],
                'avg_game_length': record['avg_game_length']
            })
        
        gateway_df = pd.DataFrame(gateway_data)
        
        # Calculate betweenness centrality for openings
        # This is a simplified version - in practice, you might want to use Neo4j's graph algorithms
        opening_centrality = {}
        for opening in gateway_df['opening_code'].unique():
            # Count how many times this opening appears in paths between other openings
            paths_through = len(transition_df[
                (transition_df['from_opening'] == opening) | 
                (transition_df['to_opening'] == opening)
            ])
            opening_centrality[opening] = paths_through
        
        gateway_df['betweenness_centrality'] = gateway_df['opening_code'].map(opening_centrality)
        
        # Identify gateway openings based on multiple criteria
        gateway_df['is_gateway'] = (
            (gateway_df['betweenness_centrality'] > gateway_df['betweenness_centrality'].quantile(0.75)) &
            (gateway_df['total_games'] > gateway_df['total_games'].median())
        )
        
        # Calculate summary statistics
        summary_stats = {
            'total_openings': len(gateway_df),
            'gateway_openings': len(gateway_df[gateway_df['is_gateway']]),
            'avg_transitions_per_opening': transition_df['transition_count'].mean(),
            'most_common_transition': transition_df.iloc[0]['from_name'] + ' → ' + transition_df.iloc[0]['to_name'],
            'highest_centrality_opening': gateway_df.loc[gateway_df['betweenness_centrality'].idxmax()]['opening_name']
        }
        
        return {
            'gateway_openings': gateway_df,
            'transition_network': transition_df,
            'summary_stats': summary_stats
        } 

    def analyze_opening_communities(self) -> Dict[str, Any]:
        """
        Analyzes how opening choices create distinct communities of players.
        Uses a bipartite graph of players and openings to identify communities
        and analyze their characteristics.
        
        Returns:
            Dict containing:
            - communities: DataFrame with community assignments and metrics
            - community_stats: Dict with community-level statistics
            - player_community_map: Dict mapping players to their communities
        """
        print("\n=== Opening Communities Analysis ===")
        print("Analyzing player communities based on opening preferences...")
        
        # First, get player-opening relationships
        player_opening_query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH p, o, count(*) as times_played
        WHERE times_played >= 3  // Only consider significant player-opening relationships
        WITH p, collect({
            opening: o.eco_code,
            name: o.name,
            times_played: times_played
        }) as openings
        WHERE size(openings) >= 5  // Only consider players with sufficient opening repertoire
        RETURN p.id as player_id,
               p.username as username,
               p.rating as rating,
               openings
        """
        
        player_results = self.db.query(player_opening_query)
        
        if not player_results:
            print("No player results found!")
            return {
                'communities': pd.DataFrame(),
                'community_stats': {},
                'player_community_map': {}
            }
        
        print(f"\nFound {len(player_results)} players with sufficient opening repertoire")
        
        # Convert to DataFrame for analysis
        player_data = []
        for record in player_results:
            player_data.append({
                'player_id': record['player_id'],
                'username': record['username'],
                'rating': record['rating'],
                'openings': record['openings']
            })
        
        player_df = pd.DataFrame(player_data)
        
        # Create a player-opening matrix for community detection
        all_openings = set()
        for openings in player_df['openings']:
            all_openings.update(op['opening'] for op in openings)
        
        print(f"Found {len(all_openings)} unique openings")
        
        # Analyze opening distribution
        opening_counts = {}
        opening_names = {}  # Store opening names
        for openings in player_df['openings']:
            for opening in openings:
                eco = opening['opening']
                if eco not in opening_counts:
                    opening_counts[eco] = 0
                    opening_names[eco] = opening['name']  # Store the name
                opening_counts[eco] += opening['times_played']
        
        print("\n=== Top 10 Most Played Openings ===")
        for opening, count in sorted(opening_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"{opening} ({opening_names[opening]}): {count} times")
        
        # Create normalized opening matrix (by player's total games)
        opening_matrix = pd.DataFrame(0.0,  # Initialize with float dtype
                                    index=player_df['player_id'],
                                    columns=list(all_openings))
        
        for idx, row in player_df.iterrows():
            total_games = sum(op['times_played'] for op in row['openings'])
            for opening in row['openings']:
                opening_matrix.loc[row['player_id'], opening['opening']] = float(opening['times_played']) / total_games
        
        # Calculate multiple similarity metrics
        from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
        
        # Cosine similarity for opening preferences
        cosine_sim = cosine_similarity(opening_matrix)
        
        # Euclidean distance for opening frequencies
        euclidean_dist = euclidean_distances(opening_matrix)
        
        # Combine similarities (normalize and weight)
        combined_similarity = 0.7 * cosine_sim + 0.3 * (1 - euclidean_dist / euclidean_dist.max())
        
        print("\n=== Similarity Metrics ===")
        print(f"Min similarity: {combined_similarity.min():.3f}")
        print(f"Max similarity: {combined_similarity.max():.3f}")
        print(f"Mean similarity: {combined_similarity.mean():.3f}")
        print(f"Std similarity: {combined_similarity.std():.3f}")
        
        # Use hierarchical clustering for more control over community formation
        from sklearn.cluster import AgglomerativeClustering
        from scipy.cluster.hierarchy import dendrogram, linkage
        
        # Calculate linkage matrix
        Z = linkage(combined_similarity, method='ward')
        
        # Try different numbers of clusters
        n_clusters_range = range(3, 8)  # Try 3 to 7 clusters
        best_n_clusters = None
        best_silhouette = -1
        
        from sklearn.metrics import silhouette_score
        
        print("\n=== Testing Different Numbers of Communities ===")
        for n_clusters in n_clusters_range:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='precomputed',
                linkage='average'
            )
            labels = clustering.fit_predict(1 - combined_similarity)  # Convert similarity to distance
            
            # Calculate silhouette score
            silhouette_avg = silhouette_score(1 - combined_similarity, labels)
            print(f"\nTesting {n_clusters} communities:")
            print(f"Silhouette score: {silhouette_avg:.3f}")
            
            if silhouette_avg > best_silhouette:
                best_silhouette = silhouette_avg
                best_n_clusters = n_clusters
                best_labels = labels
        
        print(f"\nBest number of communities: {best_n_clusters} (silhouette score: {best_silhouette:.3f})")
        
        # Apply the best clustering
        player_df['community'] = best_labels
        
        # Print community sizes and characteristics
        community_sizes = player_df['community'].value_counts()
        print("\n=== Community Sizes ===")
        for comm, size in community_sizes.items():
            print(f"Community {comm}: {size} players")
        
        # Calculate community statistics
        community_stats = {}
        for community in player_df['community'].unique():
            community_players = player_df[player_df['community'] == community]
            
            # Get common openings in this community
            community_openings = {}
            for openings in community_players['openings']:
                for opening in openings:
                    eco = opening['opening']
                    if eco not in community_openings:
                        community_openings[eco] = 0
                    community_openings[eco] += opening['times_played']
            
            # Sort openings by frequency and include names
            common_openings = sorted(community_openings.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:5]  # Top 5 openings
            
            # Add names to the common openings
            common_openings_with_names = [(eco, count, opening_names[eco]) 
                                       for eco, count in common_openings]
            
            community_stats[community] = {
                'size': len(community_players),
                'avg_rating': community_players['rating'].mean(),
                'rating_std': community_players['rating'].std(),
                'common_openings': common_openings_with_names
            }
            
            print(f"\n=== Community {community} Characteristics ===")
            print(f"Size: {len(community_players)} players")
            print(f"Average Rating: {community_players['rating'].mean():.1f} ± {community_players['rating'].std():.1f}")
            print("Top 5 Openings:")
            for eco, count, name in common_openings_with_names:
                print(f"  - {eco} ({name}): {count} times")
        
        # Create player-community mapping
        player_community_map = dict(zip(player_df['player_id'], player_df['community']))
        
        # Calculate community-level metrics
        community_metrics = {}
        for community in community_stats:
            # Get games played by community members
            community_query = """
            MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)
            WHERE p.id IN $player_ids
            WITH g, count(DISTINCT p) as community_players
            WHERE community_players >= 1
            RETURN count(g) as total_games,
                   avg(g.turns) as avg_game_length,
                   sum(CASE WHEN g.winner = 'white' THEN 1 ELSE 0 END) as white_wins,
                   sum(CASE WHEN g.winner = 'black' THEN 1 ELSE 0 END) as black_wins,
                   sum(CASE WHEN g.winner = 'draw' THEN 1 ELSE 0 END) as draws
            """
            
            community_players = player_df[player_df['community'] == community]['player_id'].tolist()
            community_results = self.db.query(community_query, {'player_ids': community_players})
            
            if community_results:
                result = community_results[0]
                community_metrics[community] = {
                    'total_games': result['total_games'],
                    'avg_game_length': result['avg_game_length'],
                    'white_win_rate': result['white_wins'] / result['total_games'],
                    'black_win_rate': result['black_wins'] / result['total_games'],
                    'draw_rate': result['draws'] / result['total_games']
                }
                
                print(f"\n=== Community {community} Game Statistics ===")
                print(f"Total Games: {result['total_games']}")
                print(f"Average Game Length: {result['avg_game_length']:.1f} moves")
                print(f"White Win Rate: {result['white_wins'] / result['total_games']:.3f}")
                print(f"Black Win Rate: {result['black_wins'] / result['total_games']:.3f}")
                print(f"Draw Rate: {result['draws'] / result['total_games']:.3f}")
        
        # Add community metrics to community stats
        for community in community_stats:
            if community in community_metrics:
                community_stats[community].update(community_metrics[community])
        
        return {
            'communities': player_df,
            'community_stats': community_stats,
            'player_community_map': player_community_map
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
