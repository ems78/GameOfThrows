import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.colors as mcolors
import pandas as pd
from pathlib import Path
from ..analysis.blunder_community import BlunderCommunityAnalysis
from ..analysis.blunder_graph_analysis import BlunderGraphAnalysis
from ..database.db_manager import Neo4jConnection
import numpy as np

class BlunderNetworkVisualization:
    """
    Visualization tools for blunder networks and communities
    """
    
    def __init__(self):
        self.analysis = BlunderCommunityAnalysis()
        self.graph_analysis = BlunderGraphAnalysis()
        self.plt = plt
        self.db = Neo4jConnection()
    
    def visualize_player_blunder_graph(self, min_edge_weight=2, figsize=(12, 10)):
        """
        Visualize the player-blunder graph
        
        Args:
            min_edge_weight: Minimum edge weight to include in visualization
            figsize: Size of the figure (width, height)
        """
        G = self.analysis.create_player_blunder_graph()
        
        # Check if graph is empty
        if len(G.nodes()) == 0:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No player blunder data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Player Blunder Network')
            plt.axis('off')
            return plt
        
        # Filter edges by weight
        edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] < min_edge_weight]
        G.remove_edges_from(edges_to_remove)
        
        # Remove isolated nodes
        isolated_nodes = list(nx.isolates(G))
        G.remove_nodes_from(isolated_nodes)
        
        # Check if graph is empty after filtering
        if len(G.nodes()) == 0:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, f"No player connections with weight >= {min_edge_weight}", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Player Blunder Network')
            plt.axis('off')
            return plt
        
        plt.figure(figsize=figsize)
        
        # Compute node sizes based on degree centrality
        centrality = nx.degree_centrality(G)
        node_sizes = [5000 * centrality[node] for node in G.nodes()]
        
        # Get edge weights for width
        edge_weights = [d['weight'] for u, v, d in G.edges(data=True)]
        
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, alpha=0.7)
        nx.draw_networkx_edges(G, pos, width=[w/5 for w in edge_weights], alpha=0.5)
        nx.draw_networkx_labels(G, pos, font_size=10)
        
        plt.title('Player Blunder Network (players connected by similar blunders)')
        plt.axis('off')
        
        return plt
    
    def visualize_communities(self, min_community_size=3, figsize=(12, 10)):
        """
        Visualize communities of players making similar blunders
        
        Args:
            min_community_size: Minimum size of communities to visualize
            figsize: Size of the figure (width, height)
        """
        G = self.analysis.create_player_blunder_graph()
        
        # Check if graph is empty
        if len(G.nodes()) == 0:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No player blunder data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Blunder Communities')
            plt.axis('off')
            return plt
        
        # Get communities
        communities = self.analysis.detect_communities(min_community_size=min_community_size)
        
        # Check if no communities were detected
        if not communities:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, f"No communities with size >= {min_community_size} detected", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Blunder Communities')
            plt.axis('off')
            return plt
        
        plt.figure(figsize=figsize)
        
        # Set up layout
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        # Generate colors for communities
        colors = list(mcolors.TABLEAU_COLORS.values())
        
        # Draw nodes by community with different colors
        for i, community in enumerate(communities):
            color = colors[i % len(colors)]
            nx.draw_networkx_nodes(G, pos, 
                                 nodelist=community,
                                 node_color=color,
                                 node_size=100,
                                 alpha=0.8,
                                 label=f"Community {i+1}")
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.2)
        
        # Draw labels for larger communities
        large_communities = [c for c in communities if len(c) >= min_community_size*2]
        for community in large_communities:
            nx.draw_networkx_labels(G, pos, 
                                  {node: node for node in community},
                                  font_size=8)
        
        plt.title(f'Blunder Communities (min size: {min_community_size})')
        plt.legend()
        plt.axis('off')
        
        return plt
    
    def visualize_opening_blunders(self, top_n=10, figsize=(12, 8)):
        """
        Visualize the most common openings with blunders.
        
        Args:
            top_n: Number of top openings to show
            figsize: Size of the figure (width, height)
        """

        query = """
        MATCH (o:Opening)<-[:USES]-(g:Game)<-[r:IN]-(b:Blunder)
        RETURN o.name as opening_name, o.eco as eco, 
               count(b) as blunder_count,
               avg(b.eval_change) as avg_eval_change,
               max(b.eval_change) as max_eval_change,
               count(DISTINCT g) as game_count
        ORDER BY blunder_count DESC
        LIMIT $top_n
        """
        
        try:
            # Execute query using Neo4jConnection
            result = list(self.db.query(query, parameters={'top_n': top_n}))
            
            if not result:
                plt.figure(figsize=figsize)
                plt.text(0.5, 0.5, "No opening blunder data available", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12)
                plt.title('Opening Blunders')
                plt.axis('off')
                return plt
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(record) for record in result])
            
            # Print column names for debugging
            print(f"Opening blunder columns: {df.columns.tolist()}")
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1])
            
            # Plot 1: Top openings by blunder count
            openings = df['opening_name'].tolist()
            blunder_counts = df['blunder_count'].tolist()
            game_counts = df['game_count'].tolist()
            
            x = np.arange(len(openings))
            width = 0.35
            
            ax1.bar(x - width/2, blunder_counts, width, label='Blunders', color='red', alpha=0.7)
            ax1.bar(x + width/2, game_counts, width, label='Games', color='blue', alpha=0.7)
            
            ax1.set_ylabel('Count')
            ax1.set_title('Top Openings by Blunder Count')
            ax1.set_xticks(x)
            ax1.set_xticklabels(openings, rotation=45, ha='right')
            ax1.legend()
            
            # Plot 2: Average evaluation change
            eval_changes = df['avg_eval_change'].tolist()
            max_eval_changes = df['max_eval_change'].tolist()
            
            ax2.bar(x - width/2, eval_changes, width, label='Avg Eval Change', color='green', alpha=0.7)
            ax2.bar(x + width/2, max_eval_changes, width, label='Max Eval Change', color='purple', alpha=0.7)
            
            ax2.set_ylabel('Evaluation Change')
            ax2.set_title('Blunder Severity by Opening')
            ax2.set_xticks(x)
            ax2.set_xticklabels(openings, rotation=45, ha='right')
            ax2.legend()
            
            # Add ECO codes as text
            for i, eco in enumerate(df['eco']):
                if pd.notna(eco):
                    ax1.text(i, 0, f'ECO: {eco}', ha='center', va='bottom')
            
            plt.tight_layout()
            return plt
            
        except Exception as e:
            print(f"Error visualizing opening blunders: {str(e)}")
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, f"Error: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Opening Blunders')
            plt.axis('off')
            return plt
    
    def visualize_weighted_blunder_graph(self, figsize=(12, 10)):
        """
        Visualize the weighted blunder graph that combines player ratings with blunder evaluation changes.
        This version calculates similarity based on shared blunders or similar blunder patterns.
        
        Args:
            figsize: Size of the figure (width, height)
        """
        try:
            # Get player data with ratings and blunder counts
            player_query = """
            MATCH (p:Player)
            OPTIONAL MATCH (p)-[:MADE_BLUNDER]->(b:Blunder)
            RETURN p.username as username, 
                   p.rating as rating,
                   count(b) as blunder_count,
                   avg(b.eval_change) as avg_eval_change,
                   max(b.eval_change) as max_eval_change
            """
            
            # Execute query using Neo4jConnection
            player_result = list(self.db.query(player_query))
            
            if not player_result:
                plt.figure(figsize=figsize)
                plt.text(0.5, 0.5, "No player data available", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12)
                plt.title('Weighted Blunder Similarity Graph')
                plt.axis('off')
                return plt
            
            # Create graph
            G = nx.Graph()
            
            # Add nodes with player data
            for record in player_result:
                G.add_node(record['username'], 
                          rating=record['rating'],
                          blunder_count=record['blunder_count'],
                          avg_eval_change=record['avg_eval_change'],
                          max_eval_change=record['max_eval_change'])
            
            # Now find similarities between players based on blunder patterns
            # We'll use a query to find players who made blunders in the same games
            # or with similar evaluation changes
            similarity_query = """
            MATCH (p1:Player)-[:MADE_BLUNDER]->(b1:Blunder)-[:IN]->(g:Game)<-[:IN]-(b2:Blunder)<-[:MADE_BLUNDER]-(p2:Player)
            WHERE p1.username < p2.username  // To avoid duplicates
            WITH p1, p2, count(DISTINCT g) as shared_games, 
                 avg(abs(b1.eval_change - b2.eval_change)) as avg_eval_diff
            RETURN p1.username as player1_username, p2.username as player2_username,
                   shared_games,
                   avg_eval_diff
            ORDER BY shared_games DESC
            """
            
            similarity_result = list(self.db.query(similarity_query))
            
            # Add edges based on similarity
            for record in similarity_result:
                # Calculate similarity score based on shared games and evaluation difference
                # Normalize the values to create a similarity score between 0 and 1
                shared_games = record['shared_games']
                eval_diff = record['avg_eval_diff'] if record['avg_eval_diff'] is not None else 10.0
                
                # Higher shared_games and lower eval_diff means higher similarity
                # We'll use a simple formula: similarity = shared_games / (1 + eval_diff)
                # This gives a score that increases with shared_games and decreases with eval_diff
                similarity = shared_games / (1 + eval_diff)
                
                # Only add edges with meaningful similarity
                if similarity > 0.5:
                    G.add_edge(record['player1_username'], 
                              record['player2_username'],
                              weight=similarity,
                              shared_games=shared_games,
                              eval_diff=eval_diff)
            
            # If we don't have enough edges, try an alternative approach
            if len(G.edges()) < 10:
                # Alternative approach: find players with similar blunder counts and evaluation changes
                alt_similarity_query = """
                MATCH (p1:Player)-[:MADE_BLUNDER]->(b1:Blunder)
                WITH p1, count(b1) as p1_blunders, avg(b1.eval_change) as p1_avg_eval
                MATCH (p2:Player)-[:MADE_BLUNDER]->(b2:Blunder)
                WHERE p1.username < p2.username
                WITH p1, p2, p1_blunders, p1_avg_eval, 
                     count(b2) as p2_blunders, avg(b2.eval_change) as p2_avg_eval
                WITH p1, p2, 
                     abs(p1_blunders - p2_blunders) as blunder_diff,
                     abs(p1_avg_eval - p2_avg_eval) as eval_diff
                RETURN p1.username as player1_username, p2.username as player2_username,
                       blunder_diff, eval_diff
                ORDER BY blunder_diff, eval_diff
                LIMIT 100
                """
                
                alt_similarity_result = list(self.db.query(alt_similarity_query))
                
                # Add edges based on alternative similarity
                for record in alt_similarity_result:
                    # Calculate similarity score based on blunder count difference and evaluation difference
                    blunder_diff = record['blunder_diff']
                    eval_diff = record['eval_diff'] if record['eval_diff'] is not None else 10.0
                    
                    # Lower differences mean higher similarity
                    # We'll use a simple formula: similarity = 1 / (1 + blunder_diff + eval_diff)
                    similarity = 1 / (1 + blunder_diff + eval_diff)
                    
                    # Only add edges with meaningful similarity
                    if similarity > 0.1:
                        G.add_edge(record['player1_username'], 
                                  record['player2_username'],
                                  weight=similarity,
                                  blunder_diff=blunder_diff,
                                  eval_diff=eval_diff)
            
            # Check if we have a valid graph
            if len(G.nodes()) == 0 or len(G.edges()) == 0:
                plt.figure(figsize=figsize)
                plt.text(0.5, 0.5, "No player similarity data available", 
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=12)
                plt.title('Weighted Blunder Similarity Graph')
                plt.axis('off')
                return plt
            
            # Rest of the visualization code remains the same
            print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges")
            
            # Set up the plot with a specific layout to accommodate the colorbar
            fig, ax = plt.subplots(figsize=figsize)
            
            # Calculate node sizes and colors
            node_sizes = []
            node_colors = []
            for node in G.nodes():
                node_data = G.nodes[node]
                node_sizes.append(node_data.get('blunder_count', 1) * 100)
                node_colors.append(node_data.get('rating', 1500))
            
            # Calculate edge weights
            edge_weights = [G[u][v]['weight'] * 3 for (u, v) in G.edges()]
            
            # Create layout
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Draw the graph
            nodes = nx.draw_networkx_nodes(G, pos, 
                                         node_size=node_sizes,
                                         node_color=node_colors,
                                         cmap=plt.cm.viridis,
                                         alpha=0.7,
                                         ax=ax)
            
            edges = nx.draw_networkx_edges(G, pos,
                                         width=edge_weights,
                                         alpha=0.5,
                                         edge_color='gray',
                                         ax=ax)
            
            # Add labels for top nodes
            node_blunders = [(node, G.nodes[node].get('blunder_count', 0)) 
                           for node in G.nodes()]
            sorted_nodes = sorted(node_blunders, key=lambda x: x[1], reverse=True)
            top_nodes = sorted_nodes[:min(10, len(sorted_nodes))]
            labels = {node: node for node, _ in top_nodes}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)
            
            # Add colorbar
            if node_colors:
                sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis,
                                         norm=plt.Normalize(vmin=min(node_colors),
                                                         vmax=max(node_colors)))
                sm.set_array([])
                cbar = plt.colorbar(sm, ax=ax)
                cbar.set_label("Player Rating")
            
            # Add legend
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                          markerfacecolor='gray',
                          markersize=8,
                          label='1-2 blunders'),
                plt.Line2D([0], [0], marker='o', color='w',
                          markerfacecolor='gray',
                          markersize=12,
                          label='3-5 blunders'),
                plt.Line2D([0], [0], marker='o', color='w',
                          markerfacecolor='gray',
                          markersize=16,
                          label='6+ blunders')
            ]
            ax.legend(handles=legend_elements,
                     loc='upper left',
                     bbox_to_anchor=(1, 1))
            
            ax.set_title("Player Blunder Similarity Network\nNode size = Blunder count, Color = Rating\nEdge thickness = Similarity strength")
            ax.axis('off')
            plt.tight_layout()
            return plt
            
        except Exception as e:
            print(f"Error visualizing weighted blunder graph: {str(e)}")
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, f"Error: {str(e)}", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Weighted Blunder Similarity Graph')
            plt.axis('off')
            return plt
    
    def visualize_rating_vs_blunder_severity(self, figsize=(10, 6)):
        """
        Create a scatter plot of player rating vs. blunder severity.
        
        Args:
            figsize: Size of the figure (width, height)
        """
        # Get player blunder statistics
        player_stats = self.graph_analysis.get_player_blunder_stats()
        
        # Convert to DataFrame
        stats_df = pd.DataFrame(player_stats)
        if stats_df.empty:
            plt.figure(figsize=figsize)
            plt.text(0.5, 0.5, "No player blunder data available", 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12)
            plt.title('Player Rating vs. Blunder Severity')
            plt.axis('off')
            return plt
        
        # Print column names for debugging
        print(f"Player stats columns: {stats_df.columns.tolist()}") # TODO: Column names are not printing correctly
        
        # Print first few rows to understand the structure
        print("First few rows of player stats:")
        print(stats_df.head())
        
        # Create scatter plot
        plt.figure(figsize=figsize)
        
        # Extract data with proper field names
        ratings = []
        eval_changes = []
        blunder_counts = []
        usernames = []
        
        # The data appears to be in a different format than expected
        # Let's try to extract it directly from the DataFrame
        for index, row in stats_df.iterrows():
            # The data seems to be in a Series format with numeric indices
            # Let's extract the values based on their position
            if len(row) >= 5:  # Ensure we have enough values
                # Based on the output, it looks like:
                # 0: username
                # 1: rating
                # 2: blunder_count
                # 3: avg_eval_change
                # 4: max_eval_change
                username = row[0]
                rating = float(row[1])
                blunder_count = int(row[2])
                avg_eval_change = float(row[3])
                
                ratings.append(rating)
                eval_changes.append(avg_eval_change)
                blunder_counts.append(blunder_count)
                usernames.append(username)
        
        # Create scatter plot
        plt.scatter(ratings, eval_changes, alpha=0.7, s=[c * 20 for c in blunder_counts])
        
        # Add labels for some points (top 5 by blunder count)
        if ratings:
            # Sort by blunder count
            sorted_indices = sorted(range(len(blunder_counts)), 
                                  key=lambda i: blunder_counts[i], 
                                  reverse=True)
            
            for i in sorted_indices[:5]:
                plt.annotate(usernames[i], # TODO: remove usernames
                            (ratings[i], eval_changes[i]),
                            xytext=(5, 5), textcoords='offset points')
        
        plt.xlabel('Player Rating')
        plt.ylabel('Average Evaluation Change (Blunder Severity)')
        plt.title('Player Rating vs. Blunder Severity\nBubble size = Number of blunders')
        plt.grid(True, alpha=0.3)
        
        # Add a trend line if there are enough points
        if len(ratings) > 1:
            z = np.polyfit(ratings, eval_changes, 1)
            p = np.poly1d(z)
            plt.plot(ratings, p(ratings), "r--", alpha=0.5, 
                    label=f"Trend: y = {z[0]:.6f}x + {z[1]:.2f}")
            plt.legend()
        
        # Add a legend for bubble sizes
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                      markersize=10, label='1 blunder'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                      markersize=20, label='2 blunders'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                      markersize=30, label='3+ blunders')
        ]
        plt.legend(handles=legend_elements, loc='upper left')
        
        plt.tight_layout()
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
