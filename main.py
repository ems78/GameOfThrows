#!/usr/bin/env python3
import os
import argparse
import time
from src.modules.database.import_data import import_data_to_neo4j, delete_all_data
from src.modules.database.queries import GraphQueries
from src.modules.visualization.network_visualization import NetworkVisualization

def parse_args():
    parser = argparse.ArgumentParser(description='Chess Network Analysis Tool')
    
    # Import arguments
    parser.add_argument('--import-data', action='store_true',
                        help='Import chess data to Neo4j')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Number of games to process in each batch (default: 1000)')
    parser.add_argument('--max-games', type=int, default=None,
                        help='Maximum number of games to import (default: all)')
    parser.add_argument('--delete-all', action='store_true',
                        help='Delete all existing data before import')
    
    # Analysis arguments
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory to save visualizations (default: output)')
    parser.add_argument('--time-window', type=str, default='monthly',
                        choices=['daily', 'weekly', 'monthly', 'yearly'],
                        help='Time window for temporal analysis (default: monthly)')
    parser.add_argument('--top-openings', type=int, default=10,
                        help='Number of top openings to show (default: 10)')
    parser.add_argument('--dpi', type=int, default=300,
                        help='DPI for saved images (default: 300)')
    parser.add_argument('--show', action='store_true',
                        help='Show visualizations instead of saving them')
    
    # Visualization types
    parser.add_argument('-v', '--visualizations', type=str, nargs='+', 
                        default=['temporal', 'opening', 'player', 'community'],
                        choices=['temporal', 'opening', 'player', 'community', 'all'],
                        help='Which visualizations to generate (default: all)')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.import_data:
        print("Starting chess data import...")
        if args.delete_all:
            print("Deleting all existing data...")
            delete_all_data()
        
        print("Waiting for Neo4j to start...")
        time.sleep(5)  # Give Neo4j time to start
        
        try:
            import_data_to_neo4j(batch_size=args.batch_size, max_games=args.max_games)
            print("Import process completed.")
        except Exception as e:
            print(f"Error during import: {str(e)}")
            import traceback
            traceback.print_exc()
            return
    
    if not args.show:
        os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize analysis components
    queries = GraphQueries()
    visualizer = NetworkVisualization()
    
    vis_types = args.visualizations
    if 'all' in vis_types:
        vis_types = ['temporal', 'opening', 'player', 'community']
    
    if 'temporal' in vis_types:
        print("Generating temporal network visualization...")
        try:
            data = queries.get_temporal_network(time_window=args.time_window)
            plt_obj = visualizer.visualize_temporal_network(data)
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/temporal_network.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating temporal network: {str(e)}")
    
    if 'opening' in vis_types:
        print("Generating opening network visualization...")
        try:
            data = queries.get_opening_network()
            plt_obj = visualizer.visualize_opening_network(data, top_n=args.top_openings)
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/opening_network.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating opening network: {str(e)}")
    
    if 'player' in vis_types:
        print("Generating player network visualization...")
        try:
            data = queries.get_player_network_metrics()
            plt_obj = visualizer.visualize_player_network(data)
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/player_network.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating player network: {str(e)}")
    
    if 'community' in vis_types:
        print("Generating community visualization...")
        try:
            data = queries.get_player_communities()
            plt_obj = visualizer.visualize_communities(data)
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/player_communities.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating community visualization: {str(e)}")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
