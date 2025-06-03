import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime

class TemporalAnalysisVisualization:
    def __init__(self):
        plt.style.use('seaborn-v0_8')
        self.colors = plt.cm.Set2(np.linspace(0, 1, 8))

    def visualize_temporal_evolution(self, data: List[Dict], time_window: str = 'monthly') -> plt.Figure:
        """
        Visualize how player networks evolve over time.
        Focuses on:
        - Network density over time
        - Emergence of distinct player groups
        - Changes in opening popularity
        
        Args:
            data: List of network snapshots over time
            time_window: Time window for analysis (daily/weekly/monthly/yearly)
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[2, 1])
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Plot 1: Network Evolution
        # Show how the number of active players and games changes over time
        ax1.plot(df['timestamp'], df['active_players'], 
                label='Active Players', color=self.colors[0])
        ax1.plot(df['timestamp'], df['total_games'], 
                label='Total Games', color=self.colors[1])
        
        # Add trend lines
        z1 = np.polyfit(range(len(df)), df['active_players'], 1)
        z2 = np.polyfit(range(len(df)), df['total_games'], 1)
        ax1.plot(df['timestamp'], np.poly1d(z1)(range(len(df))), 
                '--', alpha=0.5, color=self.colors[0])
        ax1.plot(df['timestamp'], np.poly1d(z2)(range(len(df))), 
                '--', alpha=0.5, color=self.colors[1])
        
        ax1.set_title('Network Evolution Over Time')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Count')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Opening Popularity Evolution
        # Show how the popularity of top openings changes over time
        top_openings = df['top_openings'].iloc[-1]  # Get current top openings
        for opening in top_openings[:5]:  # Show top 5 openings
            opening_data = df['opening_popularity'].apply(
                lambda x: x.get(opening, 0))
            ax2.plot(df['timestamp'], opening_data, 
                    label=opening, alpha=0.7)
        
        ax2.set_title('Evolution of Top Openings')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Usage Frequency')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def visualize_time_control_impact(self, data: List[Dict]) -> plt.Figure:
        """
        Visualize how time controls affect network structure.
        Focuses on:
        - Game duration distribution by time control
        - Network density by time control
        - Player preferences for different time controls
        
        Args:
            data: List of network metrics by time control
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Plot 1: Game Duration Distribution
        sns.boxplot(data=df, x='time_control', y='game_duration', ax=ax1)
        ax1.set_title('Game Duration by Time Control')
        ax1.set_xlabel('Time Control')
        ax1.set_ylabel('Game Duration (seconds)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Network Density by Time Control
        sns.barplot(data=df, x='time_control', y='network_density', ax=ax2)
        ax2.set_title('Network Density by Time Control')
        ax2.set_xlabel('Time Control')
        ax2.set_ylabel('Network Density')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return fig

    def visualize_opening_trends(self, data: List[Dict]) -> plt.Figure:
        """
        Visualize trends in opening usage and their impact.
        Focuses on:
        - Popularity of openings over time
        - Success rates of different openings
        - Correlation between opening choice and game outcome
        
        Args:
            data: List of opening statistics over time
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Plot 1: Opening Popularity Trends
        top_openings = df['opening_stats'].iloc[-1].nlargest(5, 'usage_count')
        for opening in top_openings.index:
            opening_data = df['opening_stats'].apply(
                lambda x: x.loc[opening, 'usage_count'])
            ax1.plot(df['timestamp'], opening_data, 
                    label=opening, alpha=0.7)
        
        ax1.set_title('Evolution of Top Openings')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Usage Count')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Opening Success Rates
        success_rates = df['opening_stats'].iloc[-1].nlargest(5, 'win_rate')
        sns.barplot(data=success_rates, x=success_rates.index, 
                   y='win_rate', ax=ax2)
        ax2.set_title('Success Rates of Top Openings')
        ax2.set_xlabel('Opening')
        ax2.set_ylabel('Win Rate')
        ax2.tick_params(axis='x', rotation=45)
        
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
