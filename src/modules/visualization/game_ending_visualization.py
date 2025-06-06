import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Any

class GameEndingVisualization:
    def __init__(self):
        self.palette = sns.color_palette("husl", 8)
    
    def visualize_ending_patterns(self, analysis_data: Dict[str, Any]) -> plt.Figure:
        """
        Create a comprehensive visualization of game ending patterns.
        """
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 12))
        gs = fig.add_gridspec(3, 2)
        
        # Distribution of game endings
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_ending_distribution(analysis_data['ending_distribution'], ax1)
        
        # Rating difference correlation
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_rating_correlation(analysis_data['rating_correlation'], ax2)
        
        # Time control impact
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_time_control_impact(analysis_data['time_control_impact'], ax3)
        
        # Win rates by ending type
        ax4 = fig.add_subplot(gs[2, :])
        self._plot_win_rates(analysis_data['win_rates'], ax4)
        
        plt.tight_layout()
        return fig
    
    def _plot_ending_distribution(self, data: Dict[str, Any], ax: plt.Axes) -> None:
        """Plot distribution of different game endings."""
        endings = list(data.keys())
        frequencies = [data[end]['frequency'] for end in endings]
        
        ax.bar(endings, frequencies, color=self.palette)
        ax.set_title('Distribution of Game Endings')
        ax.set_xlabel('Victory Status')
        ax.set_ylabel('Frequency')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _plot_rating_correlation(self, data: Dict[str, Any], ax: plt.Axes) -> None:
        """Plot correlation between rating differences and ending types."""
        endings = list(data.keys())
        means = [data[end]['mean_rating_diff'] for end in endings]
        stds = [data[end]['std_rating_diff'] for end in endings]
        
        ax.errorbar(endings, means, yerr=stds, fmt='o', color=self.palette[0])
        ax.set_title('Rating Difference by Ending Type')
        ax.set_xlabel('Victory Status')
        ax.set_ylabel('Average Rating Difference')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _plot_time_control_impact(self, data: Dict[str, Any], ax: plt.Axes) -> None:
        """Plot impact of time controls on game endings."""
        # Convert data to DataFrame format
        rows = []
        for key, values in data.items():
            time_control, status = key.split('_')
            rows.append({
                'time_control': time_control,
                'status': status,
                'frequency': values['frequency'],
                'avg_turns': values['avg_turns'],
                'avg_duration': values['avg_duration']
            })
        
        df = pd.DataFrame(rows)
        
        # Group by time control and status
        pivot = df.pivot_table(
            index='time_control',
            columns='status',
            values='frequency',
            aggfunc='sum'
        ).fillna(0)
        
        # Plot
        pivot.plot(kind='bar', ax=ax, color=self.palette)
        ax.set_title('Game Endings by Time Control')
        ax.set_xlabel('Time Control')
        ax.set_ylabel('Frequency')
        ax.legend(title='Ending Type')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _plot_win_rates(self, data: Dict[str, Any], ax: plt.Axes) -> None:
        """Plot win rates for each ending type."""
        # Convert data to DataFrame format
        rows = []
        for key, values in data.items():
            status, winner = key.split('_')
            rows.append({
                'status': status,
                'winner': winner,
                'frequency': values['frequency']
            })
        
        df = pd.DataFrame(rows)
        
        # Group by status and winner
        pivot = df.pivot_table(
            index='status',
            columns='winner',
            values='frequency',
            aggfunc='sum'
        ).fillna(0)
        
        # Plot
        pivot.plot(kind='bar', stacked=True, ax=ax, color=self.palette)
        ax.set_title('Win Rates by Ending Type')
        ax.set_xlabel('Victory Status')
        ax.set_ylabel('Frequency')
        ax.legend(title='Winner')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def show_visualization(self, fig: plt.Figure) -> None:
        """Display the visualization."""
        plt.show()
    
    def save_visualization(self, fig: plt.Figure, filename: str, dpi: int = 300) -> None:
        """Save the visualization to a file."""
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig) 
