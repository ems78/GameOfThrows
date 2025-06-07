import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List
import pandas as pd

class PlayerAnalysisVisualization:
    """Visualization class for player analysis results."""
    
    def __init__(self):
        """Initialize visualization settings."""
        self.style = 'seaborn-v0_8'  # Using a specific seaborn style version
        plt.style.use(self.style)
        self.colors = plt.cm.Set2(np.linspace(0, 1, 8))

    def visualize_rating_progression_analysis(self, results: Dict) -> plt.Figure:
        """
        Visualize the analysis of rating progression by opponent rating.
        
        Args:
            results: Dictionary containing correlation, p_value, and raw_data
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Convert raw data to DataFrame for easier plotting
        df = pd.DataFrame(results['raw_data'])
        
        # Plot 1: Rating Changes vs Opponent Rating Differences
        ax1.scatter(df['rating_diff'], df['rating_change'], 
                   alpha=0.6, color=self.colors[0])
        ax1.set_title('Rating Changes vs Opponent Rating Differences')
        ax1.set_xlabel('Opponent Rating Difference')
        ax1.set_ylabel('Rating Change')
        
        # Add correlation line
        z = np.polyfit(df['rating_diff'], df['rating_change'], 1)
        p = np.poly1d(z)
        ax1.plot(df['rating_diff'], p(df['rating_diff']), 
                "r--", alpha=0.8)
        
        # Add correlation coefficient and p-value
        ax1.text(0.05, 0.95, 
                f'Correlation: {results["correlation"]:.3f}\np-value: {results["p_value"]:.3e}',
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 2: Distribution of Rating Changes
        ax2.hist(df['rating_change'], bins=30, color=self.colors[1])
        ax2.set_title('Distribution of Rating Changes')
        ax2.set_xlabel('Rating Change')
        ax2.set_ylabel('Count')
        
        plt.tight_layout()
        return fig

    def visualize_player_prediction(self, results: Dict) -> plt.Figure:
        """
        Visualize the prediction of a player's rating progression.
        
        Args:
            results: Dictionary containing prediction results
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Rating Progression
        times = np.array(results['times'])
        ratings = np.array(results['ratings'])
        
        # Convert times to days from start
        days = (times - times[0]).astype('timedelta64[D]').astype(int)
        
        ax1.plot(days, ratings, 'b-', label='Actual Rating')
        
        # Plot prediction
        future_days = np.append(days, days[-1] + 30)  # Add 30 days for prediction
        predicted_ratings = results['predicted_rating']
        ax1.plot([days[-1], future_days[-1]], 
                [ratings[-1], predicted_ratings], 'r--', label='Predicted Rating')
        
        # Add confidence interval
        ci = results['confidence_interval']
        ax1.fill_between([days[-1], future_days[-1]],
                        [ratings[-1] - ci, predicted_ratings - ci],
                        [ratings[-1] + ci, predicted_ratings + ci],
                        color='r', alpha=0.2)
        
        ax1.set_title('Rating Progression and Prediction')
        ax1.set_xlabel('Days from Start')
        ax1.set_ylabel('Rating')
        ax1.legend()
        
        # Plot 2: Network Metrics
        metrics = results['network_metrics']
        labels = ['Centrality', 'Clustering\nCoefficient']
        values = [metrics['centrality'], metrics['clustering_coefficient']]
        
        ax2.bar(labels, values, color=self.colors[:2])
        ax2.set_title('Network Metrics')
        ax2.set_ylabel('Value')
        
        # Add regression stats
        stats = results['regression_stats']
        ax2.text(0.05, 0.95,
                f'R²: {stats["r_squared"]:.3f}\np-value: {stats["p_value"]:.3e}',
                transform=ax2.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return fig

    def visualize_network_position_analysis(self, results: Dict) -> plt.Figure:
        """
        Visualize the analysis of network position vs win rate.
        
        Args:
            results: Dictionary containing correlation results and raw data
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Convert raw data to DataFrame
        df = pd.DataFrame(results['raw_data'])
        
        # Plot 1: Win Rate vs Centrality
        ax1.scatter(df['centrality'], df['win_rate'], alpha=0.6, color=self.colors[0])
        ax1.set_title('Win Rate vs Centrality')
        ax1.set_xlabel('Betweenness Centrality')
        ax1.set_ylabel('Win Rate')
        
        # Add correlation line
        z = np.polyfit(df['centrality'], df['win_rate'], 1)
        p = np.poly1d(z)
        ax1.plot(df['centrality'], p(df['centrality']), "r--", alpha=0.8)
        
        # Add correlation stats
        centrality_stats = results['centrality_correlation']
        ax1.text(0.05, 0.95,
                f'Correlation: {centrality_stats["correlation"]:.3f}\np-value: {centrality_stats["p_value"]:.3e}',
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 2: Win Rate vs Clustering Coefficient
        ax2.scatter(df['clustering'], df['win_rate'], alpha=0.6, color=self.colors[1])
        ax2.set_title('Win Rate vs Clustering Coefficient')
        ax2.set_xlabel('Clustering Coefficient')
        ax2.set_ylabel('Win Rate')
        
        # Add correlation line
        z = np.polyfit(df['clustering'], df['win_rate'], 1)
        p = np.poly1d(z)
        ax2.plot(df['clustering'], p(df['clustering']), "r--", alpha=0.8)
        
        # Add correlation stats
        clustering_stats = results['clustering_correlation']
        ax2.text(0.05, 0.95,
                f'Correlation: {clustering_stats["correlation"]:.3f}\np-value: {clustering_stats["p_value"]:.3e}',
                transform=ax2.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return fig

    def visualize_player_analysis(self, results: Dict) -> plt.Figure:
        """
        Visualize player analysis results.
        
        Args:
            results: Dictionary containing player analysis results
            
        Returns:
            matplotlib Figure object
        """
        if not results or 'raw_data' not in results:
            raise ValueError("No valid data provided for visualization")
            
        df = pd.DataFrame(results['raw_data'])
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot rating progression
        sns.lineplot(data=df, x='game_number', y='rating', ax=ax1)
        ax1.set_title('Rating Progression')
        ax1.set_xlabel('Game Number')
        ax1.set_ylabel('Rating')
        
        # Plot win rate by opponent rating
        sns.scatterplot(data=df, x='opponent_rating', y='win_rate', ax=ax2)
        ax2.set_title('Win Rate by Opponent Rating')
        ax2.set_xlabel('Opponent Rating')
        ax2.set_ylabel('Win Rate')
        
        plt.tight_layout()
        return fig

    def save_visualization(self, fig: plt.Figure, filename: str, dpi: int = 300):
        """Save the visualization to a file."""
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    def show_visualization(self, fig: plt.Figure):
        """Display the visualization."""
        plt.show()
        plt.close(fig) 
