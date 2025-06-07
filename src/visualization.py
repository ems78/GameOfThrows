import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure

class Visualization:
    """
    Visualization tools for chess network analysis, focusing on:
    - Player Performance and Network Position Analysis
    - Opening Theory and Network Analysis
    """
    
    def __init__(self):
        """Initialize visualization settings."""
        self.style = 'seaborn-v0_8'  # Using a specific seaborn style version
        plt.style.use(self.style)
        self.colors = plt.cm.Set2(np.linspace(0, 1, 8))
    
    def visualize_network_metrics(self, results: Dict) -> plt.Figure:
        """
        Visualize network metrics vs win rate.
        
        Args:
            results: Dictionary containing network metrics and win rates
            
        Returns:
            matplotlib Figure object
        """
        if not results or 'raw_data' not in results:
            raise ValueError("No valid data provided for visualization")
            
        df = pd.DataFrame(results['raw_data'])
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot centrality vs win rate
        sns.scatterplot(data=df, x='centrality', y='win_rate', ax=ax1)
        ax1.set_title('Centrality vs Win Rate')
        ax1.set_xlabel('Centrality')
        ax1.set_ylabel('Win Rate')
        
        # Plot clustering vs win rate
        sns.scatterplot(data=df, x='clustering', y='win_rate', ax=ax2)
        ax2.set_title('Clustering vs Win Rate')
        ax2.set_xlabel('Clustering Coefficient')
        ax2.set_ylabel('Win Rate')
        
        plt.tight_layout()
        return fig
    
    def visualize_opening_performance(self, results: Dict[str, Any]) -> Figure:
        """
        Visualize opening performance analysis.
        
        Args:
            results: Dictionary containing:
                - opening_stats: DataFrame with opening performance metrics
                - player_opening_stats: DataFrame with player-specific opening performance
                - summary_stats: Dict with overall opening statistics
        
        Returns:
            matplotlib Figure object
        """
        if not results or 'opening_stats' not in results:
            raise ValueError("Invalid results format for opening performance visualization")
            
        fig = plt.figure(figsize=(15, 10))
        
        # Extract data
        opening_stats = results['opening_stats']
        summary_stats = results['summary_stats']
        
        # Create subplots
        gs = GridSpec(2, 2, figure=fig)
        
        # Plot 1: Top 10 Most Played Openings
        ax1 = fig.add_subplot(gs[0, 0])
        top_openings = opening_stats.head(10)
        sns.barplot(data=top_openings, x='games_played', y='opening_code', ax=ax1)
        ax1.set_title('Top 10 Most Played Openings')
        ax1.set_xlabel('Number of Games')
        ax1.set_ylabel('Opening Code')
        
        # Plot 2: Win Rate vs Game Length
        ax2 = fig.add_subplot(gs[0, 1])
        sns.scatterplot(data=opening_stats, x='avg_game_length', y='win_rate', alpha=0.6, ax=ax2)
        ax2.set_title('Win Rate vs Average Game Length')
        ax2.set_xlabel('Average Game Length (turns)')
        ax2.set_ylabel('Win Rate')
        
        # Plot 3: Win Rate Distribution
        ax3 = fig.add_subplot(gs[1, 0])
        sns.histplot(data=opening_stats, x='win_rate', bins=20, ax=ax3)
        ax3.set_title('Distribution of Opening Win Rates')
        ax3.set_xlabel('Win Rate')
        ax3.set_ylabel('Number of Openings')
        
        # Plot 4: Summary Statistics
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        stats_text = (
            f"Total Openings Analyzed: {summary_stats['total_openings']}\n"
            f"Total Games: {summary_stats['total_games']}\n"
            f"Average Games per Opening: {summary_stats['avg_games_per_opening']:.1f}\n\n"
            f"Most Common Opening: {summary_stats['most_common_opening']}\n"
            f"Highest Win Rate Opening: {summary_stats['highest_winrate_opening']}\n"
            f"Shortest Average Game: {summary_stats['shortest_avg_game']}\n"
            f"Longest Average Game: {summary_stats['longest_avg_game']}"
        )
        ax4.text(0.1, 0.5, stats_text, fontsize=10, va='center')
        
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
    
    def save_visualization(self, fig: plt.Figure, filename: str, dpi: int = 300) -> None:
        """
        Save visualization to file.
        
        Args:
            fig: matplotlib Figure object
            filename: Output file path
            dpi: DPI for saved image
        """
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    
    def show_visualization(self, fig: plt.Figure) -> None:
        """
        Display visualization.
        
        Args:
            fig: matplotlib Figure object
        """
        plt.show()
        plt.close(fig)
