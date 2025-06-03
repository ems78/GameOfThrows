#!/usr/bin/env python3
import os
import argparse
import time
from src.modules.database.import_data import import_data_to_neo4j, delete_all_data
from src.modules.database.queries import GraphQueries
from src.modules.visualization.network_visualization import NetworkVisualization
from src.modules.visualization.player_analysis_visualization import PlayerAnalysisVisualization
from src.modules.visualization.temporal_analysis_visualization import TemporalAnalysisVisualization
from src.modules.visualization.player_performance_visualization import PlayerPerformanceVisualization
from src.modules.analysis.player_network_analysis import PlayerNetworkAnalysis

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
                        default=['temporal', 'opening', 'player', 'community', 'performance'],
                        choices=['temporal', 'opening', 'player', 'community', 'performance', 'all'],
                        help='Which visualizations to generate (default: all)')
    
    # Player Network Analysis arguments
    parser.add_argument('--analyze-player', type=str,
                        help='Analyze a specific player\'s rating progression')
    parser.add_argument('--analyze-rating-progression', action='store_true',
                        help='Analyze rating progression by opponent rating')
    parser.add_argument('--analyze-network-position', action='store_true',
                        help='Analyze network position vs win rate')
    parser.add_argument('--analyze-time-controls', action='store_true',
                        help='Analyze impact of time controls on game dynamics')
    parser.add_argument('--analyze-opening-trends', action='store_true',
                        help='Analyze trends in opening usage and success rates')
    parser.add_argument('--output-format', type=str, default='json',
                        choices=['json', 'csv'],
                        help='Output format for analysis results (default: json)')
    parser.add_argument('--visualize-analysis', action='store_true',
                        help='Generate visualizations for the analysis results')
    
    return parser.parse_args()

def save_analysis_results(results, filename, output_format):
    """Save analysis results in the specified format."""
    if output_format == 'json':
        import json
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    elif output_format == 'csv':
        import pandas as pd
        if isinstance(results, dict) and 'raw_data' in results:
            df = pd.DataFrame(results['raw_data'])
            df.to_csv(filename, index=False)
        else:
            df = pd.DataFrame([results])
            df.to_csv(filename, index=False)

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
    network_visualizer = NetworkVisualization()
    player_analyzer = PlayerNetworkAnalysis()
    player_visualizer = PlayerAnalysisVisualization()
    temporal_visualizer = TemporalAnalysisVisualization()
    performance_visualizer = PlayerPerformanceVisualization()
    
    # Run player network analysis if requested
    if args.analyze_player:
        print(f"Analyzing rating progression for player: {args.analyze_player}")
        try:
            results = player_analyzer.predict_rating_progression(args.analyze_player)
            output_file = f'{args.output_dir}/player_analysis_{args.analyze_player}.{args.output_format}'
            save_analysis_results(results, output_file, args.output_format)
            print(f"Analysis results saved to {output_file}")
            
            if args.visualize_analysis:
                print("Generating visualization...")
                fig = player_visualizer.visualize_player_prediction(results)
                if args.show:
                    player_visualizer.show_visualization(fig)
                else:
                    player_visualizer.save_visualization(
                        fig, 
                        f'{args.output_dir}/player_prediction_{args.analyze_player}.png',
                        dpi=args.dpi
                    )
        except Exception as e:
            print(f"Error analyzing player: {str(e)}")
    
    if args.analyze_rating_progression:
        print("Analyzing rating progression by opponent rating...")
        try:
            results = player_analyzer.analyze_rating_progression_by_opponent_rating()
            output_file = f'{args.output_dir}/rating_progression_analysis.{args.output_format}'
            save_analysis_results(results, output_file, args.output_format)
            print(f"Analysis results saved to {output_file}")
            
            if args.visualize_analysis:
                print("Generating visualization...")
                fig = performance_visualizer.visualize_rating_progression(results['raw_data'])
                if args.show:
                    performance_visualizer.show_visualization(fig)
                else:
                    performance_visualizer.save_visualization(
                        fig,
                        f'{args.output_dir}/rating_progression_analysis.png',
                        dpi=args.dpi
                    )
        except Exception as e:
            print(f"Error analyzing rating progression: {str(e)}")
    
    if args.analyze_network_position:
        print("Analyzing network position vs win rate...")
        try:
            results = player_analyzer.analyze_network_position_vs_winrate()
            output_file = f'{args.output_dir}/network_position_analysis.{args.output_format}'
            save_analysis_results(results, output_file, args.output_format)
            print(f"Analysis results saved to {output_file}")
            
            if args.visualize_analysis:
                print("Generating visualization...")
                fig = performance_visualizer.visualize_network_position_impact(results['raw_data'])
                if args.show:
                    performance_visualizer.show_visualization(fig)
                else:
                    performance_visualizer.save_visualization(
                        fig,
                        f'{args.output_dir}/network_position_analysis.png',
                        dpi=args.dpi
                    )
        except Exception as e:
            print(f"Error analyzing network position: {str(e)}")
    
    if args.analyze_time_controls:
        print("Analyzing time control impact...")
        try:
            data = queries.get_time_control_metrics()
            fig = temporal_visualizer.visualize_time_control_impact(data)
            if args.show:
                temporal_visualizer.show_visualization(fig)
            else:
                temporal_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/time_control_analysis.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"Error analyzing time controls: {str(e)}")
    
    if args.analyze_opening_trends:
        print("Analyzing opening trends...")
        try:
            data = queries.get_opening_trends(time_window=args.time_window)
            fig = temporal_visualizer.visualize_opening_trends(data)
            if args.show:
                temporal_visualizer.show_visualization(fig)
            else:
                temporal_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/opening_trends_analysis.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"Error analyzing opening trends: {str(e)}")
    
    # Generate visualizations
    vis_types = args.visualizations
    if 'all' in vis_types:
        vis_types = ['temporal', 'opening', 'player', 'community', 'performance']
    
    if 'temporal' in vis_types:
        print("Generating temporal network visualization...")
        try:
            data = queries.get_temporal_network_evolution(time_window=args.time_window)
            fig = temporal_visualizer.visualize_temporal_evolution(data, time_window=args.time_window)
            if args.show:
                temporal_visualizer.show_visualization(fig)
            else:
                temporal_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/temporal_network.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"Error generating temporal network: {str(e)}")
    
    if 'opening' in vis_types:
        print("Generating opening network visualization...")
        try:
            data = queries.get_opening_network()
            fig = network_visualizer.visualize_opening_network(data, top_n=args.top_openings)
            if args.show:
                network_visualizer.show_visualization(fig)
            else:
                network_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/opening_network.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"Error generating opening network: {str(e)}")
    
    if 'player' in vis_types:
        print("Generating player network visualization...")
        try:
            data = queries.get_player_network_metrics()
            fig = network_visualizer.visualize_player_network(data)
            if args.show:
                network_visualizer.show_visualization(fig)
            else:
                network_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/player_network.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"Error generating player network: {str(e)}")
    
    if 'community' in vis_types:
        print("Generating community visualization...")
        try:
            data = queries.get_player_communities()
            fig = network_visualizer.visualize_communities(data)
            if args.show:
                network_visualizer.show_visualization(fig)
            else:
                network_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/player_communities.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"Error generating community visualization: {str(e)}")
    
    if 'performance' in vis_types:
        print("\n=== Generating Player Performance Visualization ===")
        try:
            print("Fetching player network metrics...")
            data = queries.get_player_network_metrics()
            print(f"Received {len(data)} records")
            
            print("\nCreating visualization...")
            fig = performance_visualizer.visualize_player_development(data)
            
            if args.show:
                print("\nShowing visualization...")
                performance_visualizer.show_visualization(fig)
            else:
                print("\nSaving visualization...")
                performance_visualizer.save_visualization(
                    fig,
                    f'{args.output_dir}/player_performance.png',
                    dpi=args.dpi
                )
        except Exception as e:
            print(f"\nError generating player performance visualization: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
