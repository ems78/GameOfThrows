from src.modules.database.queries import GraphQueries
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class GameEndingAnalysis:
    def __init__(self):
        self.queries = GraphQueries()

    def _convert_to_serializable(self, data: Any) -> Any:
        """Convert data to JSON serializable format."""
        if isinstance(data, dict):
            return {str(k): self._convert_to_serializable(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._convert_to_serializable(item) for item in data]
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return str(data)

    def analyze_ending_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in how games end based on network metrics.
        Returns comprehensive analysis of game endings and their correlations.
        """
        # Get game dynamics data
        game_data = self.queries.get_game_dynamics()
        
        # print("\n=== Game Ending Analysis Debug ===")
        # print(f"Raw data received: {len(game_data)} records")
        # if game_data:
        #     print("Sample record:", game_data[0])
        #     print("Record keys:", game_data[0].keys())
        
        # Convert to pandas DataFrame for easier analysis
        df = pd.DataFrame(game_data)
        
        # Rename columns based on the record keys
        if not df.empty and len(df.columns) == 8:  # We expect 8 columns
            df.columns = [
                'time_control',
                'status',
                'winner',
                'frequency',
                'avg_turns',
                'avg_rating_diff',
                'avg_duration',
                'game_details'
            ]
        
        print("\nDataFrame Info:")
        print("DataFrame shape:", df.shape)
        print("DataFrame columns:", df.columns.tolist())
        print("\nDataFrame head:")
        print(df.head())
        
        # Convert duration to seconds if it's in milliseconds
        if 'avg_duration' in df.columns:
            df['avg_duration'] = df['avg_duration'] / 1000  # Convert to seconds if in milliseconds
        
        # Basic statistics for each ending type
        ending_stats = df.groupby('status').agg({
            'frequency': 'sum',
            'avg_turns': 'mean',
            'avg_rating_diff': 'mean',
            'avg_duration': 'mean'
        }).to_dict('index')
        
        # Analyze correlation between rating difference and ending type
        rating_correlation = {}
        for status in df['status'].unique():
            status_data = df[df['status'] == status]
            rating_correlation[status] = {
                'mean_rating_diff': status_data['avg_rating_diff'].mean(),
                'std_rating_diff': status_data['avg_rating_diff'].std(),
                'count': len(status_data)
            }
        
        # Analyze time control impact on endings
        time_control_impact = {}
        for (time_control, status), group in df.groupby(['time_control', 'status']):
            time_control_impact[f"{time_control}_{status}"] = {
                'frequency': group['frequency'].sum(),
                'avg_turns': group['avg_turns'].mean(),
                'avg_duration': group['avg_duration'].mean()
            }
        
        # Calculate win rates for each ending type
        win_rates = {}
        for (status, winner), group in df.groupby(['status', 'winner']):
            win_rates[f"{status}_{winner}"] = {
                'frequency': group['frequency'].sum()
            }
        
        results = {
            'ending_distribution': ending_stats,
            'rating_correlation': rating_correlation,
            'time_control_impact': time_control_impact,
            'win_rates': win_rates,
            'raw_data': game_data
        }
        
        # Convert all data to JSON serializable format
        return self._convert_to_serializable(results)

    def get_ending_patterns_by_network_position(self) -> Dict[str, Any]:
        """
        Analyze how game endings correlate with players' network positions.
        """
        # Get player network metrics
        network_data = self.queries.get_player_network_metrics()
        
        # Get game dynamics
        game_data = self.queries.get_game_dynamics()
        
        # Combine the data to analyze patterns
        # This will show if players in different network positions
        # tend to have games end in different ways
        
        # TODO: Implement detailed network position analysis
        # This would require additional queries to get player centrality metrics
        
        return self._convert_to_serializable({
            'network_data': network_data,
            'game_data': game_data
        }) 
