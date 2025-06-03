import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List

class PlayerPerformanceVisualization:
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        self.colors = plt.cm.Set2(np.linspace(0, 1, 8))

    def visualize_rating_progression(self, data: List[Dict]) -> plt.Figure:
        """
        Visualize how players' ratings change based on their opponents' ratings.
        Focuses on:
        - Rating changes vs opponent rating differences
        - Impact of playing against higher-rated opponents
        - Long-term rating progression patterns
        
        Args:
            data: List of player rating progression data
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Plot 1: Rating Changes vs Opponent Rating Differences
        sns.scatterplot(data=df, x='rating_diff', y='rating_change', 
                       alpha=0.6, ax=ax1)
        
        # Add trend line
        z = np.polyfit(df['rating_diff'], df['rating_change'], 1)
        p = np.poly1d(z)
        ax1.plot(df['rating_diff'], p(df['rating_diff']), 
                "r--", alpha=0.8)
        
        ax1.set_title('Rating Changes vs Opponent Rating Differences')
        ax1.set_xlabel('Opponent Rating Difference')
        ax1.set_ylabel('Rating Change')
        
        # Add correlation stats
        correlation = df['rating_diff'].corr(df['rating_change'])
        ax1.text(0.05, 0.95, 
                f'Correlation: {correlation:.3f}',
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 2: Rating Progression Over Time
        # Group by time periods and calculate average rating changes
        df['time_period'] = pd.to_datetime(df['game_time']).dt.to_period('M')
        progression = df.groupby('time_period')['rating_change'].mean()
        
        ax2.plot(range(len(progression)), progression.values, 
                marker='o', alpha=0.7)
        ax2.set_title('Average Rating Changes Over Time')
        ax2.set_xlabel('Time Period')
        ax2.set_ylabel('Average Rating Change')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def visualize_network_position_impact(self, data: List[Dict]) -> plt.Figure:
        """
        Visualize how network position affects player performance.
        Focuses on:
        - Centrality vs win rate
        - Clustering coefficient vs performance
        - Network position impact on rating progression
        
        Args:
            data: List of player network metrics and performance data
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Plot 1: Centrality vs Win Rate
        sns.scatterplot(data=df, x='centrality', y='win_rate', 
                       alpha=0.6, ax=ax1)
        
        # Add trend line
        z = np.polyfit(df['centrality'], df['win_rate'], 1)
        p = np.poly1d(z)
        ax1.plot(df['centrality'], p(df['centrality']), 
                "r--", alpha=0.8)
        
        ax1.set_title('Network Centrality vs Win Rate')
        ax1.set_xlabel('Betweenness Centrality')
        ax1.set_ylabel('Win Rate')
        
        # Plot 2: Clustering Coefficient vs Rating Progression
        sns.scatterplot(data=df, x='clustering', y='rating_progression', 
                       alpha=0.6, ax=ax2)
        
        # Add trend line
        z = np.polyfit(df['clustering'], df['rating_progression'], 1)
        p = np.poly1d(z)
        ax2.plot(df['clustering'], p(df['clustering']), 
                "r--", alpha=0.8)
        
        ax2.set_title('Clustering Coefficient vs Rating Progression')
        ax2.set_xlabel('Clustering Coefficient')
        ax2.set_ylabel('Rating Progression')
        
        plt.tight_layout()
        return fig

    def visualize_player_development(self, data: List[Dict]) -> plt.Figure:
        """
        Visualize player development patterns.
        Focuses on:
        - Rating progression over time
        - Impact of game frequency on improvement
        - Success against different rating ranges
        
        Args:
            data: List of player development data
        """
        print("\n=== Player Performance Visualization Debug ===")
        print(f"Input data type: {type(data)}")
        print(f"Input data length: {len(data)}")
        if len(data) > 0:
            print(f"First record sample: {data[0]}")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Convert data to DataFrame, properly handling Neo4j records
        df = pd.DataFrame([{
            'username': record['username'],
            'current_rating': record['current_rating'],
            'initial_rating': record['initial_rating'],
            'latest_rating': record['latest_rating'],
            'win_rate': record['win_rate'],
            'total_games': record['total_games'],
            'game_history': record['game_history']
        } for record in data])
        
        print("\nDataFrame Info:")
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")
        print("\nDataFrame head:")
        print(df.head())
        print("\nDataFrame description:")
        print(df.describe())
        
        try:
            # Plot 1: Rating Progression
            # Create a scatter plot of current rating vs total games
            sns.scatterplot(data=df, x='total_games', y='current_rating', 
                          alpha=0.6, ax=ax1)
            
            # Add trend line
            z = np.polyfit(df['total_games'], df['current_rating'], 1)
            p = np.poly1d(z)
            ax1.plot(df['total_games'], p(df['total_games']), 
                    "r--", alpha=0.8)
            
            ax1.set_title('Rating vs Number of Games Played')
            ax1.set_xlabel('Total Games')
            ax1.set_ylabel('Current Rating')
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Win Rate Distribution
            print("\nCreating win rate distribution plot")
            print(f"Win rate range: {df['win_rate'].min()} to {df['win_rate'].max()}")
            sns.histplot(data=df, x='win_rate', bins=20, ax=ax2)
            ax2.set_title('Distribution of Win Rates')
            ax2.set_xlabel('Win Rate')
            ax2.set_ylabel('Count')
            
            plt.tight_layout()
            print("\nVisualization completed successfully")
            return fig
            
        except Exception as e:
            print(f"\nError in visualization: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    def save_visualization(self, fig: plt.Figure, filename: str, dpi: int = 300):
        """Save the visualization to a file."""
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    def show_visualization(self, fig: plt.Figure):
        """Display the visualization."""
        plt.show()
        plt.close(fig) 
