#!/usr/bin/env python3
"""
Blunder Graph Analysis

This script analyzes the relationship between player ratings and blunder severity
by creating a weighted graph where players are connected based on their blunder patterns.
"""

import sys
import os
import pandas as pd
import networkx as nx
import numpy as np
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(str(Path(__file__).resolve().parents[2]))

from modules.database.models import GraphModels

class BlunderGraphAnalysis:
    """
    Analyzes the relationship between player ratings and blunder severity.
    """
    
    def __init__(self):
        self.models = GraphModels()
    
    def get_player_blunder_stats(self):
        """
        Returns statistics about player blunders including:
        - Average evaluation change
        - Maximum evaluation change
        - Number of blunders
        - Rating at time of blunders
        """
        return self.models.get_player_blunder_stats()
    
    def create_weighted_blunder_graph(self):
        """
        Creates a weighted graph analysis that combines player ratings with blunder evaluation changes.
        """
        return self.models.create_weighted_blunder_graph()
    
    def build_networkx_graph(self):
        """
        Builds a NetworkX graph from the weighted blunder data.
        
        Returns:
            tuple: (NetworkX graph, DataFrame with player statistics)
        """
        # Get player blunder statistics
        player_stats = self.get_player_blunder_stats()
        
        # Convert to DataFrame for easier manipulation
        stats_df = pd.DataFrame(player_stats)
        if stats_df.empty:
            print("No player statistics found. Make sure data has been imported.")
            return None, None
        
        # Print column names for debugging
        print(f"Player stats columns: {stats_df.columns.tolist()}")
        
        # Create the weighted graph
        graph_data = self.create_weighted_blunder_graph()
        
        # Convert to DataFrame
        graph_df = pd.DataFrame(graph_data)
        if graph_df.empty:
            print("No graph data found. Make sure players have made blunders.")
            return None, stats_df
        
        # Print column names for debugging
        print(f"Graph data columns: {graph_df.columns.tolist()}")
        
        # Create a NetworkX graph for visualization
        G = nx.Graph()
        
        # Add nodes (players)
        for _, row in stats_df.iterrows():
            # Check if the required fields exist
            if 'username' not in row and 'p.username' not in row:
                print(f"Warning: 'username' field not found in row: {row}")
                continue
                
            if 'rating' not in row and 'p.rating' not in row:
                print(f"Warning: 'rating' field not found in row: {row}")
                continue
                
            if 'blunder_count' not in row:
                print(f"Warning: 'blunder_count' field not found in row: {row}")
                continue
                
            if 'avg_eval_change' not in row:
                print(f"Warning: 'avg_eval_change' field not found in row: {row}")
                continue
            
            # Use the correct field names
            username = row.get('username', row.get('p.username'))
            rating = float(row.get('rating', row.get('p.rating')))
            blunder_count = row['blunder_count']
            avg_eval_change = row['avg_eval_change']
            
            G.add_node(username, 
                      rating=rating, 
                      blunder_count=blunder_count,
                      avg_eval_change=avg_eval_change)
        
        # Add edges (relationships between players)
        for _, row in graph_df.iterrows():
            # Check if the required fields exist
            if 'player1_username' not in row or 'player2_username' not in row:
                print(f"Warning: player username fields not found in row: {row}")
                continue
                
            if 'weight' not in row or 'rating_diff' not in row:
                print(f"Warning: weight or rating_diff fields not found in row: {row}")
                continue
            
            # Use the correct field names
            player1 = row['player1_username']
            player2 = row['player2_username']
            weight = float(row['weight'])
            rating_diff = float(row['rating_diff'])
            
            # Only add edge if both nodes exist
            if G.has_node(player1) and G.has_node(player2):
                G.add_edge(player1, player2, weight=weight, rating_diff=rating_diff)
        
        return G, stats_df
    
    def analyze_graph(self, G, stats_df):
        """
        Perform additional analysis on the graph and return insights.
        
        Returns:
            dict: Dictionary containing analysis results
        """
        if G is None or stats_df is None or G.number_of_nodes() == 0:
            return {"error": "No graph data available for analysis"}
        
        results = {}
        
        # Calculate graph metrics
        results["node_count"] = G.number_of_nodes()
        results["edge_count"] = G.number_of_edges()
        
        # Find the most connected players
        degree_dict = dict(G.degree())
        top_connected = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        results["top_connected_players"] = [{"player": player, "connections": degree} for player, degree in top_connected]
        
        # Find communities in the graph
        communities = list(nx.community.greedy_modularity_communities(G))
        results["community_count"] = len(communities)
        
        # Analyze the relationship between rating and blunder severity
        correlation = stats_df['p.rating'].astype(float).corr(stats_df['avg_eval_change'].astype(float))
        results["rating_blunder_correlation"] = correlation
        
        # Determine correlation interpretation
        if correlation < 0:
            results["correlation_interpretation"] = "Higher-rated players tend to make less severe blunders."
        elif correlation > 0:
            results["correlation_interpretation"] = "Higher-rated players tend to make more severe blunders."
        else:
            results["correlation_interpretation"] = "There is no clear correlation between player rating and blunder severity."
        
        # Find the most severe blunders by rating range
        stats_df['rating_range'] = pd.cut(stats_df['p.rating'].astype(float), 
                                         bins=[0, 1500, 2000, 2500, 3000, float('inf')],
                                         labels=['<1500', '1500-2000', '2000-2500', '2500-3000', '>3000'])
        
        rating_range_stats = stats_df.groupby('rating_range')['avg_eval_change'].mean().sort_values(ascending=False)
        results["blunder_severity_by_rating"] = rating_range_stats.to_dict()
        
        return results

def run_analysis():
    """
    Run the weighted graph analysis and print the results.
    """
    print("Running weighted blunder graph analysis...")
    
    # Initialize the analysis
    analysis = BlunderGraphAnalysis()
    
    # Get player blunder statistics
    print("Fetching player blunder statistics...")
    player_stats = analysis.get_player_blunder_stats()
    
    # Convert to DataFrame for easier manipulation
    stats_df = pd.DataFrame(player_stats)
    if not stats_df.empty:
        print(f"Found {len(stats_df)} players with blunders")
        print("\nTop 10 players by average evaluation change:")
        print(stats_df.head(10).to_string())
    else:
        print("No player statistics found. Make sure data has been imported.")
        return
    
    # Build the NetworkX graph
    print("\nBuilding NetworkX graph...")
    G, stats_df = analysis.build_networkx_graph()
    
    if G is None:
        print("Failed to build graph. Make sure players have made blunders.")
        return
    
    print(f"Created graph with {G.number_of_nodes()} players and {G.number_of_edges()} relationships")
    
    # Analyze the graph
    print("\nAnalyzing graph...")
    results = analysis.analyze_graph(G, stats_df)
    
    # Print insights
    print("\nGraph Analysis Insights:")
    print(f"Number of players (nodes): {results['node_count']}")
    print(f"Number of relationships (edges): {results['edge_count']}")
    
    print("\nMost connected players (by number of similar blunder patterns):")
    for player_data in results["top_connected_players"]:
        print(f"  {player_data['player']}: {player_data['connections']} connections")
    
    print(f"\nNumber of player communities: {results['community_count']}")
    
    print(f"\nCorrelation between player rating and blunder severity: {results['rating_blunder_correlation']:.4f}")
    print(f"  {results['correlation_interpretation']}")
    
    print("\nAverage blunder severity by rating range:")
    for rating_range, severity in results["blunder_severity_by_rating"].items():
        print(f"  {rating_range}: {severity:.4f}")
    
    print("\nAnalysis complete! Use the visualization module to visualize the results.")

if __name__ == "__main__":
    run_analysis() 
