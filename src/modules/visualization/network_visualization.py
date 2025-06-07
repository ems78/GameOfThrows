import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.colors as mcolors
import pandas as pd
from pathlib import Path
import numpy as np
from datetime import datetime
import seaborn as sns
from typing import Dict, List

class NetworkVisualization:
    """
    Visualization tools for chess network analysis, focusing on:
    - Temporal network evolution
    - Player performance and network position
    - Opening theory and network analysis
    - Game dynamics and network properties
    """
    
    def __init__(self):
        """Initialize visualization settings."""
        self.style = 'seaborn-v0_8'  # Using a specific seaborn style version
        plt.style.use(self.style)
        self.colors = plt.cm.Set2(np.linspace(0, 1, 8))
        self.plt = plt
    
    def visualize_temporal_network(self, data, figsize=(12, 10)):
        """
        Visualize player connections and game counts.
        
        Args:
            data: Query results from get_temporal_network
            figsize: Size of the figure (width, height)
        """
        try:
            if not data:
                print("Temporal network data is empty")
                plt.figure(figsize=figsize)
                plt.text(0.5, 0.5, "No network data available", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12)
                plt.title('Player Network')
                plt.axis('off')
                return plt
            
            print(f"Temporal network data received: {len(data)} records")
            # Convert data to DataFrame
            df = pd.DataFrame([dict(record) for record in data])
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"Sample data:\n{df.head()}")
            
            # Create figure
            plt.figure(figsize=figsize)
            
            # Create graph
            G = nx.Graph()
            
            # Add edges with weights based on games played
            for _, row in df.iterrows():
                G.add_edge(row['player1'], row['player2'], weight=row['games_played'])
            
            print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            
            # Calculate node sizes based on degree centrality
            centrality = nx.degree_centrality(G)
            node_sizes = [5000 * centrality[node] for node in G.nodes()]
            
            # Get edge weights for width
            edge_weights = [G[u][v]['weight'] for (u, v) in G.edges()]
            
            # Draw the network
            pos = nx.spring_layout(G, k=0.3, iterations=50)
            nx.draw_networkx_nodes(G, pos, node_size=node_sizes, alpha=0.7)
            nx.draw_networkx_edges(G, pos, width=[w/5 for w in edge_weights], alpha=0.5)
            nx.draw_networkx_labels(G, pos, font_size=8)
            
            plt.title('Player Network\nNode size = Centrality, Edge width = Games played')
            plt.axis('off')
            
            plt.tight_layout()
            return plt
        except Exception as e:
            print(f"Error in visualize_temporal_network: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def visualize_opening_network(self, data, top_n=10, figsize=(12, 8)):
        """
        Visualize the network of openings and their usage patterns.
        
        Args:
            data: Query results from get_opening_network
            top_n: Number of top openings to show
            figsize: Size of the figure (width, height)
        """
        try:
            if not data:
                print("Opening network data is empty")
                plt.figure(figsize=figsize)
                plt.text(0.5, 0.5, "No opening network data available", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12)
                plt.title('Opening Network')
                plt.axis('off')
                return plt
            
            print(f"Opening network data received: {len(data)} records")
            # Convert data to DataFrame
            df = pd.DataFrame([dict(record) for record in data])
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"Sample data:\n{df.head()}")
            
            # Create figure
            plt.figure(figsize=figsize)
            
            # Calculate usage for each opening
            df['usage_count'] = df['player_usage'].apply(len)
            
            # Get top openings by usage
            top_openings = df.nlargest(top_n, 'usage_count')
            openings = [f"{row['o.eco_code']}\n{row['o.name']}" for _, row in top_openings.iterrows()]
            usage = top_openings['usage_count'].tolist()
            
            print(f"Top {top_n} openings: {openings}")
            print(f"Usage counts: {usage}")
            
            # Create horizontal bar chart
            plt.barh(range(len(openings)), usage)
            plt.yticks(range(len(openings)), openings)
            plt.title(f'Top {top_n} Openings by Usage')
            plt.xlabel('Number of Players')
            
            plt.tight_layout()
            return plt
        except Exception as e:
            print(f"Error in visualize_opening_network: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def visualize_player_network(self, data, figsize=(12, 10)):
        """
        Visualize player network metrics including rating progression and win rates.
        
        Args:
            data: Query results from get_player_network_metrics
            figsize: Size of the figure (width, height)
        """
        if not data:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No player network data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Player Network')
            plt.axis('off')
            return plt
        
        # Convert data to DataFrame
        df = pd.DataFrame([dict(record) for record in data])
        print(f"Player network data columns: {df.columns.tolist()}")
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1])
        
        # Plot 1: Player network with rating progression
        G = nx.Graph()
        
        # Add nodes for players
        for _, row in df.iterrows():
            G.add_node(row['username'],
                      rating=row['current_rating'],
                      games_played=row['total_games'],
                      rating_progression=row['latest_rating'] - row['initial_rating'],
                      win_rate=row['win_rate'])
        
        # Calculate node sizes based on games played
        node_sizes = [G.nodes[node]['games_played'] * 50 for node in G.nodes()]
        
        # Calculate node colors based on rating progression
        node_colors = [G.nodes[node]['rating_progression'] for node in G.nodes()]
        
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        nodes = nx.draw_networkx_nodes(G, pos, 
                                     node_size=node_sizes,
                                     node_color=node_colors,
                                     cmap=plt.cm.RdBu,
                                     alpha=0.7,
                                     ax=ax1)
        
        nx.draw_networkx_labels(G, pos, font_size=8, ax=ax1)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdBu,
                                 norm=plt.Normalize(vmin=min(node_colors),
                                                 vmax=max(node_colors)))
        sm.set_array([])
        plt.colorbar(sm, ax=ax1, label='Rating Progression')
        
        ax1.set_title('Player Network\nNode size = Games played, Color = Rating progression')
        ax1.axis('off')
        
        # Plot 2: Win rate vs. Games played
        ax2.scatter(df['total_games'], 
                   df['win_rate'],
                   alpha=0.7,
                   c=df['current_rating'],
                   cmap=plt.cm.viridis)
        
        ax2.set_xlabel('Games Played')
        ax2.set_ylabel('Win Rate')
        ax2.set_title('Win Rate vs. Games Played\nColor = Current Rating')
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis,
                                 norm=plt.Normalize(vmin=min(df['current_rating']),
                                                 vmax=max(df['current_rating'])))
        sm.set_array([])
        plt.colorbar(sm, ax=ax2, label='Current Rating')
        
        plt.tight_layout()
        return plt
    
    def visualize_communities(self, data, figsize=(15, 10)):
        """
        Visualize player communities based on their game interactions.
        Focuses on research-relevant metrics:
        - Rating progression within communities
        - Opening patterns and preferences
        - Game outcomes and time control effects
        
        Args:
            data: Query results from get_player_communities
            figsize: Size of the figure (width, height)
        """
        try:
            if not data:
                print("Community data is empty")
                plt.figure(figsize=figsize)
                plt.text(0.5, 0.5, "No community data available", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12)
                plt.title('Player Communities')
                plt.axis('off')
                return plt
            
            print(f"Community data received: {len(data)} records")
            # Convert data to DataFrame
            df = pd.DataFrame([dict(record) for record in data])
            print(f"DataFrame columns: {df.columns.tolist()}")
            
            # Create graph
            G = nx.Graph()
            
            # Add edges with weights based on games played
            for _, row in df.iterrows():
                G.add_edge(row['player1'], row['player2'], weight=row['games_played'])
            
            print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            
            # Detect communities using Louvain method from community module
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(G)
            except ImportError:
                print("Python-Louvain package not found, using connected components instead")
                communities = {}
                for i, component in enumerate(nx.connected_components(G)):
                    for node in component:
                        communities[node] = i
            
            # Analyze communities
            community_stats = {}
            for node, comm_id in communities.items():
                if comm_id not in community_stats:
                    community_stats[comm_id] = {
                        'size': 0,
                        'players': set(),
                        'total_games': 0,
                        'rating_progression': [],
                        'openings': {},
                        'time_controls': {},
                        'game_outcomes': {'white_wins': 0, 'black_wins': 0, 'draws': 0},
                        'avg_rating_diff': 0,
                        'centrality': 0
                    }
                community_stats[comm_id]['size'] += 1
                community_stats[comm_id]['players'].add(node)
                
                # Get player's games from the graph
                player_games = G[node]
                community_stats[comm_id]['total_games'] += len(player_games)
                
                # Calculate centrality for this player
                community_stats[comm_id]['centrality'] += nx.degree_centrality(G)[node]
            
            # Calculate community metrics
            for comm_id in community_stats:
                stats = community_stats[comm_id]
                if stats['size'] > 0:
                    stats['centrality'] /= stats['size']  # Average centrality
                    stats['avg_games_per_player'] = stats['total_games'] / stats['size']
            
            # Sort communities by size and get top 10
            top_communities = sorted(community_stats.items(), 
                                  key=lambda x: x[1]['size'], 
                                  reverse=True)[:10]
            
            print(f"Found {len(community_stats)} communities")
            
            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
            
            # Plot 1: Community sizes
            sizes = [stats['size'] for _, stats in top_communities]
            ax1.bar(range(len(sizes)), sizes)
            ax1.set_title('Top 10 Communities by Size')
            ax1.set_xlabel('Community ID')
            ax1.set_ylabel('Number of Players')
            ax1.set_xticks(range(len(sizes)))
            ax1.set_xticklabels([f'Comm {i+1}' for i in range(len(sizes))], rotation=45)
            
            # Plot 2: Average centrality
            centrality = [stats['centrality'] for _, stats in top_communities]
            ax2.bar(range(len(centrality)), centrality)
            ax2.set_title('Average Player Centrality in Communities')
            ax2.set_xlabel('Community ID')
            ax2.set_ylabel('Average Centrality')
            ax2.set_xticks(range(len(centrality)))
            ax2.set_xticklabels([f'Comm {i+1}' for i in range(len(centrality))], rotation=45)
            
            # Plot 3: Games per player vs Community size
            games_per_player = [stats['avg_games_per_player'] for _, stats in top_communities]
            ax3.scatter(sizes, games_per_player)
            ax3.set_title('Games per Player vs Community Size')
            ax3.set_xlabel('Community Size')
            ax3.set_ylabel('Average Games per Player')
            
            # Plot 4: Community connectivity (edges per node)
            edges_per_node = [stats['total_games'] / stats['size'] for _, stats in top_communities]
            ax4.bar(range(len(edges_per_node)), edges_per_node)
            ax4.set_title('Community Connectivity')
            ax4.set_xlabel('Community ID')
            ax4.set_ylabel('Edges per Node')
            ax4.set_xticks(range(len(edges_per_node)))
            ax4.set_xticklabels([f'Comm {i+1}' for i in range(len(edges_per_node))], rotation=45)
            
            plt.tight_layout()
            
            # Add text summary of top communities
            summary_text = "Top 5 Communities Analysis:\n\n"
            for i, (comm_id, stats) in enumerate(top_communities[:5], 1):
                top_players = sorted(stats['players'], 
                                  key=lambda x: G.degree(x), 
                                  reverse=True)[:3]
                summary_text += (f"Community {i}:\n"
                               f"  Size: {stats['size']} players\n"
                               f"  Total games: {stats['total_games']}\n"
                               f"  Avg games/player: {stats['avg_games_per_player']:.1f}\n"
                               f"  Avg centrality: {stats['centrality']:.3f}\n"
                               f"  Top players: {', '.join(top_players)}\n\n")
            
            # Add text box with summary
            plt.figtext(0.02, 0.02, summary_text, 
                       bbox=dict(facecolor='white', alpha=0.8),
                       fontsize=8)
            
            print("Visualization complete")
            return plt
        except Exception as e:
            print(f"Error in visualize_communities: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
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
