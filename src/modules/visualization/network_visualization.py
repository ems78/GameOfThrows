import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.colors as mcolors
import pandas as pd
from pathlib import Path
import numpy as np
from datetime import datetime

class NetworkVisualization:
    """
    Visualization tools for chess network analysis, focusing on:
    - Temporal network evolution
    - Player performance and network position
    - Opening theory and network analysis
    - Game dynamics and network properties
    """
    
    def __init__(self):
        self.plt = plt
    
    def visualize_temporal_network(self, data, figsize=(12, 10)):
        """
        Visualize how player networks evolve over time.
        
        Args:
            data: Query results from get_temporal_network
            figsize: Size of the figure (width, height)
        """
        if not data:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No temporal network data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Temporal Network Evolution')
            plt.axis('off')
            return plt
        
        # Convert data to DataFrame
        df = pd.DataFrame([dict(record) for record in data])
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1])
        
        # Plot 1: Network evolution over time
        G = nx.Graph()
        
        # Add nodes and edges for each time window
        for _, row in df.iterrows():
            G.add_edge(row['player1'], row['player2'], 
                      weight=row['games_played'],
                      time_window=row['time_window'])
        
        # Calculate node sizes based on degree centrality
        centrality = nx.degree_centrality(G)
        node_sizes = [5000 * centrality[node] for node in G.nodes()]
        
        # Get edge weights for width
        edge_weights = [G[u][v]['weight'] for (u, v) in G.edges()]
        
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, alpha=0.7, ax=ax1)
        nx.draw_networkx_edges(G, pos, width=[w/5 for w in edge_weights], alpha=0.5, ax=ax1)
        nx.draw_networkx_labels(G, pos, font_size=8, ax=ax1)
        
        ax1.set_title('Player Network Evolution')
        ax1.axis('off')
        
        # Plot 2: Game frequency over time
        time_series = df.groupby('time_window')['games_played'].sum()
        time_series.plot(kind='line', ax=ax2, marker='o')
        ax2.set_title('Game Frequency Over Time')
        ax2.set_xlabel('Time Window')
        ax2.set_ylabel('Number of Games')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return plt
    
    def visualize_opening_network(self, data, top_n=10, figsize=(12, 8)):
        """
        Visualize the network of openings and their usage patterns.
        
        Args:
            data: Query results from get_opening_network
            top_n: Number of top openings to show
            figsize: Size of the figure (width, height)
        """
        if not data:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No opening network data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Opening Network')
            plt.axis('off')
            return plt
        
        # Convert data to DataFrame
        df = pd.DataFrame([dict(record) for record in data])
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1])
        
        # Plot 1: Opening usage network
        G = nx.Graph()
        
        # Add nodes for openings
        for _, row in df.iterrows():
            G.add_node(row['o.eco_code'], 
                      name=row['o.name'],
                      ply=row['o.ply'],
                      usage=len(row['player_usage']))
        
        # Add edges between openings used by the same players
        for _, row in df.iterrows():
            players = [p['player'] for p in row['player_usage']]
            for i, player1 in enumerate(players):
                for player2 in players[i+1:]:
                    if G.has_edge(player1, player2):
                        G[player1][player2]['weight'] += 1
                    else:
                        G.add_edge(player1, player2, weight=1)
        
        # Calculate node sizes based on usage
        node_sizes = [G.nodes[node]['usage'] * 100 for node in G.nodes()]
        
        # Get edge weights for width
        edge_weights = [G[u][v]['weight'] for (u, v) in G.edges()]
        
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, alpha=0.7, ax=ax1)
        nx.draw_networkx_edges(G, pos, width=[w/5 for w in edge_weights], alpha=0.5, ax=ax1)
        nx.draw_networkx_labels(G, pos, font_size=8, ax=ax1)
        
        ax1.set_title('Opening Usage Network')
        ax1.axis('off')
        
        # Plot 2: Top openings by usage
        top_openings = df.nlargest(top_n, lambda x: [len(p['player_usage']) for p in x])
        openings = [f"{row['o.eco_code']}\n{row['o.name']}" for _, row in top_openings.iterrows()]
        usage = [len(row['player_usage']) for _, row in top_openings.iterrows()]
        
        ax2.barh(range(len(openings)), usage)
        ax2.set_yticks(range(len(openings)))
        ax2.set_yticklabels(openings)
        ax2.set_title(f'Top {top_n} Openings by Usage')
        ax2.set_xlabel('Number of Players')
        
        plt.tight_layout()
        return plt
    
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
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1])
        
        # Plot 1: Player network with rating progression
        G = nx.Graph()
        
        # Add nodes for players
        for _, row in df.iterrows():
            G.add_node(row['p.username'],
                      rating=row['p.rating'],
                      games_played=row['games_played'],
                      rating_progression=row['latest_rating'] - row['initial_rating'],
                      win_rate=row['wins'] / row['games_played'] if row['games_played'] > 0 else 0)
        
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
        ax2.scatter(df['games_played'], 
                   df['wins'] / df['games_played'],
                   alpha=0.7,
                   c=df['p.rating'],
                   cmap=plt.cm.viridis)
        
        ax2.set_xlabel('Games Played')
        ax2.set_ylabel('Win Rate')
        ax2.set_title('Win Rate vs. Games Played\nColor = Current Rating')
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis,
                                 norm=plt.Normalize(vmin=min(df['p.rating']),
                                                 vmax=max(df['p.rating'])))
        sm.set_array([])
        plt.colorbar(sm, ax=ax2, label='Current Rating')
        
        plt.tight_layout()
        return plt
    
    def visualize_communities(self, data, figsize=(12, 10)):
        """
        Visualize player communities based on their game interactions.
        
        Args:
            data: Query results from get_player_communities
            figsize: Size of the figure (width, height)
        """
        if not data:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No community data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Player Communities')
            plt.axis('off')
            return plt
        
        # Convert data to DataFrame
        df = pd.DataFrame([dict(record) for record in data])
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes with community information
        for _, row in df.iterrows():
            G.add_node(row['player'], community=row['communityId'])
        
        # Get unique communities
        communities = df['communityId'].unique()
        
        plt.figure(figsize=figsize)
        
        # Generate colors for communities
        colors = list(mcolors.TABLEAU_COLORS.values())
        
        # Draw nodes by community with different colors
        for i, community in enumerate(communities):
            community_nodes = [node for node in G.nodes() 
                             if G.nodes[node]['community'] == community]
            color = colors[i % len(colors)]
            nx.draw_networkx_nodes(G, 
                                 nx.spring_layout(G, k=0.3, iterations=50),
                                 nodelist=community_nodes,
                                 node_color=color,
                                 node_size=100,
                                 alpha=0.8,
                                 label=f"Community {i+1}")
        
        # Draw labels for all nodes
        nx.draw_networkx_labels(G, 
                              nx.spring_layout(G, k=0.3, iterations=50),
                              font_size=8)
        
        plt.title('Player Communities')
        plt.legend()
        plt.axis('off')
        
        return plt
    
    def save_visualization(self, plt_obj, filename, dpi=300):
        """Save a visualization to a file"""
        try:
            plt_obj.savefig(filename, dpi=dpi, bbox_inches='tight')
            print(f"Visualization saved to {filename}")
        except Exception as e:
            print(f"Error saving visualization to {filename}: {str(e)}")
        finally:
            plt_obj.close()
        
    def show_visualization(self, plt_obj):
        """Display a visualization"""
        try:
            plt_obj.show()
        except Exception as e:
            print(f"Error displaying visualization: {str(e)}")
        finally:
            plt_obj.close() 
