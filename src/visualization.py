import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

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
        Visualize network metrics vs win rate with enhanced chess-specific insights.
        
        Args:
            results: Dictionary containing network metrics and win rates
            
        Returns:
            matplotlib Figure object
        """
        if not results or 'raw_data' not in results:
            raise ValueError("No valid data provided for visualization")
            
        df = pd.DataFrame(results['raw_data'])
        
        # Verify required columns exist
        required_columns = ['centrality', 'win_rate', 'opening_diversity', 'clustering', 
                          'avg_game_length', 'time_control_variety']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(2, 2)
        
        # 1. Network Position vs Win Rate (with opening diversity)
        ax1 = fig.add_subplot(gs[0, 0])
        
        # Normalize centrality to 0-1 range for better color visibility
        centrality_min = df['centrality'].min()
        centrality_max = df['centrality'].max()
        centrality_range = centrality_max - centrality_min
        normalized_centrality = (df['centrality'] - centrality_min) / centrality_range
        
        scatter = ax1.scatter(df['centrality'], df['win_rate'], 
                            c=normalized_centrality,  # Use normalized values
                            s=100,
                            cmap='viridis',
                            alpha=0.7)  # Slightly increased alpha for better visibility
        
        # Add colorbar with original centrality values
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('Centrality (normalized)')
        
        # Add actual centrality values to colorbar ticks
        ticks = np.linspace(0, 1, 5)  # 5 ticks
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f'{centrality_min + t * centrality_range:.3f}' for t in ticks])
        
        ax1.set_title('Network Position vs Win Rate\n(color=centrality)')
        ax1.set_xlabel('Centrality')
        ax1.set_ylabel('Win Rate')
        
        # Add a grid for better readability
        ax1.grid(True, linestyle='--', alpha=0.3)
        
        # 2. Rating Range Analysis
        ax2 = fig.add_subplot(gs[0, 1])
        if 'rating_range_stats' in results:
            rating_stats = pd.DataFrame(results['rating_range_stats']).T
            rating_stats[['avg_win_rate', 'avg_centrality', 'avg_clustering']].plot(
                kind='bar', ax=ax2, width=0.8)
            ax2.set_title('Metrics by Rating Range')
            ax2.set_xlabel('Rating Range')
            ax2.set_ylabel('Average Value')
            ax2.legend(['Win Rate', 'Centrality', 'Clustering'])
            plt.xticks(rotation=45)
        else:
            ax2.text(0.5, 0.5, 'Rating range statistics not available',
                    ha='center', va='center')
            ax2.set_title('Rating Range Analysis (No Data)')
        
        # 3. Game Length vs Network Position
        ax3 = fig.add_subplot(gs[1, 0])
        sns.scatterplot(data=df, x='avg_game_length', y='win_rate',
                       hue='clustering', size='centrality',
                       sizes=(20, 200), ax=ax3)
        ax3.set_title('Game Length vs Win Rate\n(size=centrality, color=clustering)')
        ax3.set_xlabel('Average Game Length (moves)')
        ax3.set_ylabel('Win Rate')
        
        # 4. Time Control Analysis
        ax4 = fig.add_subplot(gs[1, 1])
        
        # Use time control data from the results
        if 'time_control_variety' in df.columns:
            # Filter data to include only time control varieties up to 11
            filtered_df = df[df['time_control_variety'] <= 11].copy()
            
            # Create a box plot of win rates grouped by time control variety
            sns.boxplot(data=filtered_df, x='time_control_variety', y='win_rate', ax=ax4)
            ax4.set_title('Win Rate by Time Control Variety\n(up to 11 different controls)')
            ax4.set_xlabel('Number of Different Time Controls')
            ax4.set_ylabel('Win Rate')
            
            # Add a horizontal line at 0.5 for reference
            ax4.axhline(y=0.5, color='r', linestyle='--', alpha=0.3)
            
            # Add grid for better readability
            ax4.grid(True, linestyle='--', alpha=0.3, axis='y')
            
            # Add count labels
            counts = filtered_df['time_control_variety'].value_counts().sort_index()
            for i, count in enumerate(counts):
                ax4.text(i, ax4.get_ylim()[0], f'n={count}',
                        ha='center', va='bottom', rotation=0)
        else:
            ax4.text(0.5, 0.5, 'Time control data not available',
                    ha='center', va='center')
            ax4.set_title('Time Control Analysis (No Data)')
        
        # Add correlation coefficients as text
        corr_text = []
        for metric in ['centrality', 'clustering', 'opening_diversity']:
            if f'{metric}_correlation' in results:
                corr = results[f'{metric}_correlation']
                corr_text.append(
                    f"{metric.title()}: {corr['correlation']:.2f} "
                    f"(p={corr['p_value']:.2e})"
                )
        
        if corr_text:
            fig.text(0.02, 0.02, "Correlations with Win Rate:\n" + "\n".join(corr_text),
                    fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return fig
    
    def visualize_opening_performance(self, results: Dict[str, Any]) -> Figure:
        """
        Visualize opening performance analysis and community patterns.
        
        Args:
            results: Dictionary containing:
                - opening_stats: DataFrame with opening performance metrics
                - rating_level_stats: DataFrame with performance by rating level
                - transition_stats: DataFrame with opening transition patterns
                - summary_stats: Dict with overall opening statistics
        
        Returns:
            matplotlib Figure object
        """
        if not results or 'opening_stats' not in results:
            raise ValueError("Invalid results format for opening performance visualization")
            
        fig = plt.figure(figsize=(15, 12))
        
        # Extract data
        opening_stats = results['opening_stats']
        rating_level_stats = results['rating_level_stats']
        transition_stats = results['transition_stats']
        summary_stats = results['summary_stats']
        
        # Create subplots
        gs = GridSpec(2, 2, figure=fig)
        
        # Plot 1: Win Rate by Rating Level
        ax1 = fig.add_subplot(gs[0, 0])
        rating_pivot = rating_level_stats.pivot_table(
            index='opening_code',
            columns=['rating_level', 'color'],
            values='win_rate'
        ).head(10)  # Top 10 openings
        rating_pivot.plot(kind='bar', ax=ax1)
        ax1.set_title('Win Rate by Rating Level and Color (Top 10 Openings)')
        ax1.set_xlabel('Opening Code')
        ax1.set_ylabel('Win Rate')
        ax1.legend(title='Rating Level & Color')
        plt.xticks(rotation=45)
        
        # Plot 2: Opening Transitions
        ax2 = fig.add_subplot(gs[0, 1])
        top_transitions = transition_stats.head(10)
        sns.barplot(data=top_transitions, x='transition_count', y='from_opening', ax=ax2)
        ax2.set_title('Top 10 Opening Transitions')
        ax2.set_xlabel('Number of Transitions')
        ax2.set_ylabel('From Opening')
        
        # Plot 3: Win Rate vs Game Length (White only)
        ax3 = fig.add_subplot(gs[1, 0])
        
        # Filter for white statistics only
        white_stats = opening_stats[opening_stats['color'] == 'white']
        
        # Create the scatter plot
        sns.scatterplot(
            data=white_stats,
            x='avg_game_length',
            y='win_rate',
            size='games_played',
            alpha=0.6,
            ax=ax3
        )
        
        # Add trend line
        sns.regplot(
            data=white_stats,
            x='avg_game_length',
            y='win_rate',
            scatter=False,
            ax=ax3,
            color='red',
            line_kws={'linestyle': '--'}
        )
        
        ax3.set_title('Win Rate vs Average Game Length (White)')
        ax3.set_xlabel('Average Game Length (turns)')
        ax3.set_ylabel('Win Rate')
        ax3.set_ylim(0, 1)  # Set y-axis limits to 0-1 for win rate
        
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
    
    def visualize_gateway_openings(self, results: Dict[str, Any]) -> Figure:
        """
        Visualize gateway openings analysis.
        
        Args:
            results: Dictionary containing:
                - gateway_openings: DataFrame with gateway opening metrics
                - transition_network: DataFrame with opening transition statistics
                - summary_stats: Dict with overall gateway opening statistics
        
        Returns:
            matplotlib Figure object
        """
        if not results or 'gateway_openings' not in results:
            raise ValueError("Invalid results format for gateway openings visualization")
            
        fig = plt.figure(figsize=(15, 10))
        
        # Extract data
        gateway_df = results['gateway_openings']
        transition_df = results['transition_network']
        summary_stats = results['summary_stats']
        
        # Create subplots
        gs = GridSpec(2, 2, figure=fig)
        
        # Plot 1: Gateway Openings by Betweenness Centrality
        ax1 = fig.add_subplot(gs[0, 0])
        gateway_openings = gateway_df[gateway_df['is_gateway']]
        
        # Get top 5 and bottom 5 by centrality
        top_gateways = gateway_openings.nlargest(5, 'betweenness_centrality')
        bottom_gateways = gateway_openings.nsmallest(5, 'betweenness_centrality')
        
        # Combine and sort for visualization
        combined_gateways = pd.concat([top_gateways, bottom_gateways])
        combined_gateways = combined_gateways.sort_values('betweenness_centrality', ascending=True)
        
        # Create a horizontal bar plot with normalized centrality
        max_centrality = combined_gateways['betweenness_centrality'].max()
        min_centrality = combined_gateways['betweenness_centrality'].min()
        normalized_centrality = (combined_gateways['betweenness_centrality'] - min_centrality) / (max_centrality - min_centrality) * 100
        
        # Create the bar plot
        bars = ax1.barh(combined_gateways['opening_name'], normalized_centrality)
        
        # Color the bars based on whether they're top or bottom
        for i, bar in enumerate(bars):
            if i < 5:  # Bottom 5
                bar.set_color('lightcoral')
            else:  # Top 5
                bar.set_color('lightgreen')
        
        # Add value labels on the bars with transition counts
        for i, bar in enumerate(bars):
            width = bar.get_width()
            opening_name = combined_gateways['opening_name'].iloc[i]
            transitions = combined_gateways['total_games'].iloc[i]
            ax1.text(width + 1, bar.get_y() + bar.get_height()/2,
                    f'{width:.1f}% ({transitions} games)', va='center')
        
        ax1.set_title('Top and Bottom 5 Gateway Openings by Centrality')
        ax1.set_xlabel('Relative Centrality (%)')
        ax1.set_ylabel('Opening')
        
        # Rotate y-axis labels for better readability
        plt.setp(ax1.get_yticklabels(), rotation=0, ha='right')
        
        # Add grid for better readability
        ax1.grid(True, axis='x', alpha=0.3)
        
        # Add a concise text box with explanation
        explanation = (
            "Gateway openings bridge different opening systems.\n"
            "Higher centrality = more connections between openings.\n"
            "Numbers show relative centrality and total games."
        )
        ax1.text(0.02, 0.98, explanation,
                transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Plot 2: Win Rates by Color for Gateway Openings
        ax2 = fig.add_subplot(gs[0, 1])
        gateway_winrates = gateway_openings[['opening_name', 'white_win_rate', 'black_win_rate']]
        gateway_winrates = gateway_winrates.melt(
            id_vars=['opening_name'],
            value_vars=['white_win_rate', 'black_win_rate'],
            var_name='Color',
            value_name='Win Rate'
        )
        sns.boxplot(data=gateway_winrates, x='Color', y='Win Rate', ax=ax2)
        ax2.set_title('Win Rate Distribution by Color for Gateway Openings')
        ax2.set_xlabel('Color')
        ax2.set_ylabel('Win Rate')
        
        # Plot 3: Most Common Opening Transitions
        ax3 = fig.add_subplot(gs[1, 0])
        top_transitions = transition_df.head(10)
        sns.barplot(data=top_transitions,
                   x='transition_count',
                   y='from_name',
                   ax=ax3)
        ax3.set_title('Top 10 Most Common Opening Transitions')
        ax3.set_xlabel('Number of Transitions')
        ax3.set_ylabel('From Opening')
        
        # Plot 4: Summary Statistics
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        stats_text = (
            f"Total Openings Analyzed: {summary_stats['total_openings']}\n"
            f"Number of Gateway Openings: {summary_stats['gateway_openings']}\n"
            f"Average Transitions per Opening: {summary_stats['avg_transitions_per_opening']:.1f}\n\n"
            f"Most Common Transition: {summary_stats['most_common_transition']}\n"
            f"Highest Centrality Opening: {summary_stats['highest_centrality_opening']}"
        )
        ax4.text(0.1, 0.5, stats_text, fontsize=10, va='center')
        
        plt.tight_layout()
        return fig
    
    def visualize_opening_communities(self, results: Dict[str, Any]) -> Figure:
        """
        Visualize opening communities analysis.
        
        Args:
            results: Dictionary containing:
                - communities: DataFrame with community assignments and metrics
                - community_stats: Dict with community-level statistics
                - player_community_map: Dict mapping players to their communities
        
        Returns:
            matplotlib Figure object
        """
        if not results or 'communities' not in results:
            raise ValueError("Invalid results format for opening communities visualization")
            
        fig = plt.figure(figsize=(15, 10))
        
        # Extract data
        communities_df = results['communities']
        community_stats = results['community_stats']
        
        # Create subplots
        gs = GridSpec(2, 2, figure=fig)
        
        # Plot 1: Community Size Distribution
        ax1 = fig.add_subplot(gs[0, 0])
        community_sizes = [stats['size'] for stats in community_stats.values()]
        sns.histplot(community_sizes, bins=20, ax=ax1)
        ax1.set_title('Distribution of Community Sizes')
        ax1.set_xlabel('Number of Players')
        ax1.set_ylabel('Number of Communities')
        
        # Plot 2: Average Rating by Community
        ax2 = fig.add_subplot(gs[0, 1])
        community_ratings = [(comm_id, stats['avg_rating']) 
                           for comm_id, stats in community_stats.items()]
        community_ratings_df = pd.DataFrame(community_ratings, 
                                          columns=['Community', 'Average Rating'])
        sns.barplot(data=community_ratings_df, 
                   x='Community', 
                   y='Average Rating',
                   ax=ax2)
        ax2.set_title('Average Rating by Community')
        ax2.set_xlabel('Community ID')
        ax2.set_ylabel('Average Rating')
        
        # Plot 3: Win Rate Distribution by Community
        ax3 = fig.add_subplot(gs[1, 0])
        win_rates = []
        for comm_id, stats in community_stats.items():
            if 'white_win_rate' in stats:
                win_rates.append({
                    'Community': comm_id,
                    'Color': 'White',
                    'Win Rate': stats['white_win_rate']
                })
                win_rates.append({
                    'Community': comm_id,
                    'Color': 'Black',
                    'Win Rate': stats['black_win_rate']
                })
        
        if win_rates:
            win_rates_df = pd.DataFrame(win_rates)
            
            # Create a color map for communities
            community_colors = plt.cm.tab10(np.linspace(0, 1, len(community_stats)))
            
            # Plot each community's win rates with colored dots
            for comm_id in win_rates_df['Community'].unique():
                comm_data = win_rates_df[win_rates_df['Community'] == comm_id]
                color = community_colors[comm_id]
                
                # Plot white win rate
                white_data = comm_data[comm_data['Color'] == 'White']
                ax3.scatter(white_data['Community'], white_data['Win Rate'], 
                          color='white', edgecolor=color, s=100, label=f'Community {comm_id} (White)')
                
                # Plot black win rate
                black_data = comm_data[comm_data['Color'] == 'Black']
                ax3.scatter(black_data['Community'], black_data['Win Rate'], 
                          color=color, s=100, label=f'Community {comm_id} (Black)')
                
                # Add connecting line between white and black win rates
                ax3.plot([comm_id, comm_id], 
                        [white_data['Win Rate'].iloc[0], black_data['Win Rate'].iloc[0]], 
                        color=color, linestyle='--', alpha=0.5)
            
            ax3.set_xlabel('Community')
            ax3.set_ylabel('Win Rate')
            ax3.set_title('Win Rate Distribution by Community')
            ax3.grid(True, alpha=0.3)
            
            # Set x-axis to show only community IDs
            ax3.set_xticks(list(community_stats.keys()))
            
            # Add a horizontal line at 0.5 to show equal win rate
            ax3.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5)
            
            # Rotate x-axis labels for better readability
            plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
            
            # Adjust legend to show only unique community colors
            handles, labels = ax3.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax3.legend(by_label.values(), by_label.keys(), 
                      bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot 4: Common Openings by Community
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        common_openings_text = "Most Common Openings by Community:\n\n"
        for comm_id, stats in community_stats.items():
            common_openings_text += f"Community {comm_id}:\n"
            for eco, count, name in stats['common_openings']:
                common_openings_text += f"  - {eco} ({name}): {count} games\n"
            common_openings_text += "\n"
        ax4.text(0.1, 0.5, common_openings_text, fontsize=8, va='center')
        
        plt.tight_layout()
        return fig
    
    def visualize_rating_progression(self, results: Dict) -> Figure:
        """
        Visualize rating progression analysis.
        
        Args:
            results: Dictionary containing:
                - correlation: Correlation between rating difference and change
                - p_value: Statistical significance
                - sample_size: Number of games analyzed
                - raw_data: List of rating progression data points
        
        Returns:
            matplotlib Figure object
        """
        if not results or 'raw_data' not in results:
            raise ValueError("Invalid results format for rating progression visualization")
            
        # Create a figure with multiple subplots
        fig = plt.figure(figsize=(20, 15))
        gs = gridspec.GridSpec(3, 2, height_ratios=[1, 1, 1])
        
        # Plot 1: Overall Rating Distribution
        ax1 = fig.add_subplot(gs[0, :])
        
        # Define rating bands
        rating_bands = {
            'Grandmaster': (2500, float('inf')),
            'International Master': (2400, 2500),
            'FIDE Master': (2300, 2400),
            'Candidate Master': (2200, 2300),
            'Class A': (2000, 2200),
            'Class B': (1800, 2000),
            'Class C': (1600, 1800),
            'Class D': (1400, 1600),
            'Class E': (1200, 1400),
            'Class F': (1000, 1200),
            'Beginner': (0, 1000)
        }
        
        # Plot rating distribution first
        df = pd.DataFrame(results['raw_data'])
        sns.histplot(data=df, x='player_rating', bins=50, ax=ax1)
        
        # Add rating bands as background with proper scaling
        y_max = ax1.get_ylim()[1]  # Get the maximum y value from the histogram
        for category, (min_rating, max_rating) in rating_bands.items():
            if min_rating <= df['player_rating'].max():  # Only draw bands up to max rating
                ax1.axvspan(min_rating, min(max_rating, df['player_rating'].max()), 
                          alpha=0.1, color='gray')
                # Add category label inside the plot
                if min_rating < df['player_rating'].max():
                    ax1.text(min_rating + (min(max_rating, df['player_rating'].max()) - min_rating)/2,
                            y_max * 0.95,  # Position at 95% of the y-axis height
                            category,
                            rotation=90,
                            va='top',
                            ha='center',
                            alpha=0.5)
        
        ax1.set_title('Distribution of Player Ratings')
        ax1.set_xlabel('Player Rating')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        
        # Adjust x-axis limits to match data
        ax1.set_xlim(0, df['player_rating'].max() * 1.05)  # Add 5% padding
        
        # Plot 2: Rating Change Distribution
        ax2 = fig.add_subplot(gs[1, 0])
        sns.histplot(data=df, x='rating_change', bins=50, ax=ax2)
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax2.set_title('Distribution of Rating Changes')
        ax2.set_xlabel('Rating Change')
        ax2.set_ylabel('Frequency')
        
        # Plot 3: Rating Change vs Rating Difference
        ax3 = fig.add_subplot(gs[1, 1])
        sns.scatterplot(data=df, x='rating_diff', y='rating_change', 
                       alpha=0.3, ax=ax3)
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax3.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        ax3.set_title('Rating Change vs Rating Difference')
        ax3.set_xlabel('Rating Difference (Opponent - Player)')
        ax3.set_ylabel('Rating Change')
        
        # Plot 4: Performance by Rating Range
        ax4 = fig.add_subplot(gs[2, 0])
        df['rating_range'] = pd.cut(df['player_rating'], 
                                  bins=[0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, float('inf')],
                                  labels=['<1000', '1000-1200', '1200-1400', '1400-1600', 
                                        '1600-1800', '1800-2000', '2000-2200', '2200-2400', '2400+'])
        # Fix FutureWarning by explicitly setting observed=True
        performance_by_range = df.groupby('rating_range', observed=True)['rating_change'].agg(['mean', 'std', 'count'])
        
        # Handle any infinite values in the data
        performance_by_range = performance_by_range.replace([np.inf, -np.inf], np.nan)
        
        # Plot only if we have valid data
        if not performance_by_range.empty and not performance_by_range['mean'].isna().all():
            performance_by_range['mean'].plot(kind='bar', ax=ax4, yerr=performance_by_range['std'])
            ax4.set_title('Average Rating Change by Rating Range')
            ax4.set_xlabel('Rating Range')
            ax4.set_ylabel('Average Rating Change')
            plt.xticks(rotation=45)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data for rating range analysis', 
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Average Rating Change by Rating Range')
        
        # Plot 5: Top Players Analysis
        ax5 = fig.add_subplot(gs[2, 1])
        # Get top 5 players by number of games
        top_players = df['player'].value_counts().head(5).index
        top_players_data = df[df['player'].isin(top_players)]
        
        # Calculate average rating change for each player
        player_stats = top_players_data.groupby('player').agg({
            'rating_change': ['mean', 'std', 'count'],
            'player_rating': 'mean'
        }).round(2)
        
        # Create a table with player statistics
        ax5.axis('off')
        table_data = []
        for player in top_players:
            stats = player_stats.loc[player]
            table_data.append([
                player,
                f"{stats[('player_rating', 'mean')]:.0f}",
                f"{stats[('rating_change', 'mean')]:.2f}",
                f"{stats[('rating_change', 'std')]:.2f}",
                f"{stats[('rating_change', 'count')]}"
            ])
        
        table = ax5.table(
            cellText=table_data,
            colLabels=['Player', 'Avg Rating', 'Avg Change', 'Std Dev', 'Games'],
            loc='center',
            cellLoc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        ax5.set_title('Top 5 Players by Number of Games')
        
        plt.tight_layout()
        return fig
    
    def visualize_opening_network_metrics(self, results: Dict) -> Figure:
        """
        Visualize opening network position analysis.
        
        Args:
            results: Dictionary containing:
                - opening_metrics: Dict with opening-specific metrics
                - total_openings_analyzed: Total number of openings analyzed
        
        Returns:
            matplotlib Figure object
        """
        if not results or 'opening_metrics' not in results:
            raise ValueError("Invalid results format for opening network metrics visualization")
            
        fig = plt.figure(figsize=(15, 10))
        
        # Extract data
        metrics = results['opening_metrics']
        data = []
        for opening, stats in metrics.items():
            data.append({
                'opening': opening,
                'name': stats['name'],
                'player_count': stats['player_count'],
                'avg_win_rate': stats['avg_win_rate'],
                'avg_games_played': stats['avg_games_played'],
                'correlation': stats['correlation'],
                'p_value': stats['p_value']
            })
        
        df = pd.DataFrame(data)
        
        # Create subplots
        gs = GridSpec(2, 2, figure=fig)
        
        # Plot 1: Win Rate vs Games Played
        ax1 = fig.add_subplot(gs[0, 0])
        sns.scatterplot(data=df, x='avg_games_played', y='avg_win_rate', 
                       size='player_count', sizes=(50, 400), alpha=0.6, ax=ax1)
        ax1.set_title('Win Rate vs Games Played')
        ax1.set_xlabel('Average Games Played')
        ax1.set_ylabel('Average Win Rate')
        
        # Plot 2: Top Openings by Player Count
        ax2 = fig.add_subplot(gs[0, 1])
        
        # Get top 10 openings by player count
        top_openings = df.nlargest(10, 'player_count')
        
        # Create horizontal bar plot
        bars = ax2.barh(top_openings['name'], top_openings['player_count'])
        
        # Add player count labels at the end of each bar
        for bar in bars:
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{int(width)}', 
                    ha='left', va='center', fontsize=9)
        
        ax2.set_title('Top 10 Most Played Openings')
        ax2.set_xlabel('Number of Players')
        ax2.set_ylabel('Opening')
        
        # Rotate y-axis labels for better readability
        plt.setp(ax2.get_yticklabels(), rotation=0, ha='right')
        
        # Add summary statistics as text
        stats_text = (
            f"Total Openings: {len(df)}\n"
            f"Average Players per Opening: {df['player_count'].mean():.1f}\n"
            f"Median Players per Opening: {df['player_count'].median():.1f}"
        )
        ax2.text(0.95, 0.05, stats_text,
                transform=ax2.transAxes,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 3: Correlation vs P-value
        ax3 = fig.add_subplot(gs[1, 0])
        sns.scatterplot(data=df, x='correlation', y='p_value', 
                       size='player_count', sizes=(50, 400), alpha=0.6, ax=ax3)
        ax3.set_title('Correlation vs P-value')
        ax3.set_xlabel('Correlation')
        ax3.set_ylabel('P-value')
        
        # Plot 4: Summary Statistics
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        stats_text = (
            f"Total Openings Analyzed: {results['total_openings_analyzed']}\n"
            f"Average Players per Opening: {df['player_count'].mean():.1f}\n"
            f"Average Win Rate: {df['avg_win_rate'].mean():.3f}\n"
            f"Average Games Played: {df['avg_games_played'].mean():.1f}\n\n"
            f"Top 3 Openings by Player Count:\n"
        )
        top_openings = df.nlargest(3, 'player_count')
        for _, row in top_openings.iterrows():
            stats_text += f"- {row['name']}: {row['player_count']} players\n"
        
        ax4.text(0.1, 0.5, stats_text, fontsize=10, va='center')
        
        plt.tight_layout()
        return fig
    
    def visualize_game_dynamics(self, results: Dict) -> Figure:
        """
        Visualize game dynamics analysis.
        
        Args:
            results: Dictionary containing:
                - Game dynamics metrics by victory status
                - Statistical correlations
                - Performance patterns
        
        Returns:
            matplotlib Figure object
        """
        if not results:
            raise ValueError("Invalid results format for game dynamics visualization")
            
        fig = plt.figure(figsize=(15, 10))
        
        # Create subplots
        gs = GridSpec(2, 2, figure=fig)
        
        # Define color scheme for victory statuses
        status_colors = {
            'mate': '#FF6B6B',      # Red
            'resign': '#4ECDC4',    # Teal
            'outoftime': '#FFD93D',  # Yellow
            'draw': '#95A5A6'       # Gray
        }
        
        # Extract data for each victory status
        statuses = ['mate', 'resign', 'outoftime', 'draw']
        data = []
        for status in statuses:
            if status in results:
                data.append({
                    'status': status,
                    'avg_game_length': results[status]['avg_game_length'],
                    'avg_rating_diff': results[status]['avg_rating_diff'],
                    'total_games': results[status]['total_games'],
                    'player_count': results[status]['player_count']
                })
        
        df = pd.DataFrame(data)
        
        # Plot 1: Game Length by Victory Status
        ax1 = fig.add_subplot(gs[0, 0])
        bars1 = sns.barplot(data=df, x='status', y='avg_game_length', ax=ax1, palette=status_colors)
        ax1.set_title('Average Game Length by Victory Status')
        ax1.set_xlabel('Victory Status')
        ax1.set_ylabel('Average Game Length (turns)')
        
        # Add value labels on top of bars
        for bar in bars1.patches:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{bar.get_height():.1f}',
                    ha='center', va='bottom')
        
        # Plot 2: Rating Difference by Victory Status
        ax2 = fig.add_subplot(gs[0, 1])
        bars2 = sns.barplot(data=df, x='status', y='avg_rating_diff', ax=ax2, palette=status_colors)
        ax2.set_title('Average Rating Difference by Victory Status')
        ax2.set_xlabel('Victory Status')
        ax2.set_ylabel('Average Rating Difference')
        
        # Add value labels on top of bars
        for bar in bars2.patches:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{bar.get_height():.1f}',
                    ha='center', va='bottom')
        
        # Plot 3: Game Distribution
        ax3 = fig.add_subplot(gs[1, 0])
        bars3 = sns.barplot(data=df, x='status', y='total_games', ax=ax3, palette=status_colors)
        ax3.set_title('Number of Games by Victory Status')
        ax3.set_xlabel('Victory Status')
        ax3.set_ylabel('Number of Games')
        
        # Add value labels on top of bars
        for bar in bars3.patches:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{int(bar.get_height())}',
                    ha='center', va='bottom')
        
        # Plot 4: Correlations Summary
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        correlations_text = "Correlations between Game Length and Rating Difference:\n\n"
        for status in statuses:
            if status in results.get('correlations', {}):
                corr = results['correlations'][status]
                correlations_text += (
                    f"{status.upper()}:\n"
                    f"  Correlation: {corr['correlation']:.3f}\n"
                    f"  P-value: {corr['p_value']:.3f}\n\n"
                )
        ax4.text(0.1, 0.5, correlations_text, fontsize=10, va='center')
        
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
