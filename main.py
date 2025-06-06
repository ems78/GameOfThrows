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
from src.modules.visualization.game_ending_visualization import GameEndingVisualization
from src.modules.analysis.player_network_analysis import PlayerNetworkAnalysis
from src.modules.analysis.game_ending_analysis import GameEndingAnalysis

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
    
    # Add new argument for game ending analysis
    parser.add_argument('--analyze-game-endings', action='store_true',
                        help='Analyze patterns in how games end based on network metrics')
    
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
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Chess Network Analysis Tool')
    parser.add_argument('--analyze-game-endings', action='store_true', help='Analyze game ending patterns')
    parser.add_argument('--output-dir', type=str, default='output', help='Directory for output files')
    parser.add_argument('--output-format', type=str, default='json', choices=['json', 'csv'], help='Output format for analysis results')
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    if args.analyze_game_endings:
        print("Analyzing game ending patterns...")
        
        # Initialize analysis and visualization components
        game_ending_analysis = GameEndingAnalysis()
        game_ending_visualizer = GameEndingVisualization()
        
        # Perform analysis
        results = game_ending_analysis.analyze_ending_patterns()
        
        # Save analysis results
        output_file = os.path.join(args.output_dir, 'game_ending_analysis.json')
        save_analysis_results(results, output_file, args.output_format)
        
        # Generate and save visualization
        print("Generating visualization...")
        fig = game_ending_visualizer.visualize_ending_patterns(results)
        game_ending_visualizer.save_visualization(fig, os.path.join(args.output_dir, 'game_ending_analysis.png'))
        
        print("Analysis complete!")

if __name__ == "__main__":
    main()
