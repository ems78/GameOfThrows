#!/usr/bin/env python3
"""
Chess Network Analysis Tool

This script provides functionality for analyzing chess games, focusing on:
1. Player Performance and Network Position Analysis
2. Opening Theory and Network Analysis

The analysis explores how player network positions affect their performance and development,
and how opening choices create distinct communities and influence game outcomes.
"""

import os
import argparse
import json
from typing import Dict, Any
import pandas as pd
import numpy as np

from src.database.import_data import import_data_to_neo4j, delete_all_data
from src.visualization import Visualization
from src.analysis import Analysis

class ChessAnalysisConfig:
    """Configuration class for chess analysis parameters."""
    
    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize configuration from command line arguments."""
        # Data import settings
        self.import_data = args.import_data
        self.batch_size = args.batch_size
        self.max_games = args.max_games
        self.delete_all = args.delete_all
        
        # Output settings
        self.output_dir = args.output_dir
        self.output_format = args.output_format
        self.dpi = args.dpi
        self.show = args.show
        
        # Analysis settings
        self.analyze = args.analyze
        
def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Chess Network Analysis Tool')
    
    # Data import arguments
    parser.add_argument('--import-data', action='store_true',
                       help='Import chess data to Neo4j')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Number of games to process in each batch (default: 1000)')
    parser.add_argument('--max-games', type=int, default=None,
                       help='Maximum number of games to import (default: all)')
    parser.add_argument('--delete-all', action='store_true',
                       help='Delete all existing data before import')
    
    # Output settings
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Directory to save visualizations')
    parser.add_argument('--output-format', type=str, default='png',
                       choices=['png', 'pdf', 'svg'],
                       help='Output format for visualizations')
    parser.add_argument('--dpi', type=int, default=300,
                       help='DPI for saved images (default: 300)')
    parser.add_argument('--show', action='store_true',
                       help='Show visualizations instead of saving them')
    
    # Analysis settings
    parser.add_argument('--analyze', action='store_true',
                       help='Run analysis')
    
    return parser.parse_args()

def save_analysis_results(results: Dict[str, Any], filename: str, output_format: str) -> None:
    """
    Save analysis results in the specified format.
    
    Args:
        results: Analysis results to save
        filename: Output file path
        output_format: Format to save results in ('json' or 'csv')
    """
    def convert_to_serializable(obj):
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, dict):
            return {str(k): convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
            return obj.item()
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (set,)):
            return list(obj)
        return obj

    if output_format == 'json':
        serializable_results = convert_to_serializable(results)
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
    elif output_format == 'csv':
        if isinstance(results, dict) and 'raw_data' in results:
            df = pd.DataFrame(results['raw_data'])
        else:
            df = pd.DataFrame([results])
        df.to_csv(filename, index=False)

def run_analysis(config: ChessAnalysisConfig) -> Dict[str, Any]:
    """Run network position analysis and return results."""
    analysis = Analysis()
    
    print("Starting analysis...")
    
    results = {
        'network_metrics': analysis.analyze_network_position_vs_winrate(),
        'opening_performance': analysis.analyze_opening_performance(),
        'gateway_openings': analysis.analyze_gateway_openings(),
        'opening_communities': analysis.analyze_opening_communities(),
        'rating_progression': analysis.analyze_rating_progression_by_opponent_rating(),
        'opening_network_position': analysis.analyze_opening_network_position(),
        'game_dynamics': analysis.analyze_network_position_vs_game_dynamics()
    }
    
    return results

def main():
    """Main entry point for the chess analysis tool."""
    args = parse_arguments()
    config = ChessAnalysisConfig(args)
    
    # Create output directory if it doesn't exist
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Run data import if requested
    if config.import_data:
        print("Importing data to Neo4j...")
        if config.delete_all:
            delete_all_data()
        import_data_to_neo4j(
            batch_size=config.batch_size,
            max_games=config.max_games
        )
    
    # Initialize visualization
    visualizer = Visualization()
    
    if config.analyze:
        results = run_analysis(config)
        
        # Save results as JSON
        output_file = os.path.join(config.output_dir, 'analysis_results.json')
        save_analysis_results(results, output_file, 'json')
        print(f"Analysis results saved to {output_file}")
        
        # Generate and save visualizations
        if results:
            print("Generating visualizations...")
            # Network metrics visualization
            if 'network_metrics' in results:
                fig1 = visualizer.visualize_network_metrics(results['network_metrics'])
                visualizer.save_visualization(
                    fig1,
                    os.path.join(config.output_dir, 'network_metrics.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig1)
            
            # Opening performance visualization
            if 'opening_performance' in results:
                fig2 = visualizer.visualize_opening_performance(results['opening_performance'])
                visualizer.save_visualization(
                    fig2,
                    os.path.join(config.output_dir, 'opening_performance.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig2)
            
            # Gateway openings visualization
            if 'gateway_openings' in results:
                fig3 = visualizer.visualize_gateway_openings(results['gateway_openings'])
                visualizer.save_visualization(
                    fig3,
                    os.path.join(config.output_dir, 'gateway_openings.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig3)
            
            # Opening communities visualization
            if 'opening_communities' in results:
                fig4 = visualizer.visualize_opening_communities(results['opening_communities'])
                visualizer.save_visualization(
                    fig4,
                    os.path.join(config.output_dir, 'opening_communities.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig4)
            
            # Rating progression visualization
            if 'rating_progression' in results:
                fig5 = visualizer.visualize_rating_progression(results['rating_progression'])
                visualizer.save_visualization(
                    fig5,
                    os.path.join(config.output_dir, 'rating_progression.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig5)
            
            # Opening network position visualization
            if 'opening_network_position' in results:
                fig6 = visualizer.visualize_opening_network_metrics(results['opening_network_position'])
                visualizer.save_visualization(
                    fig6,
                    os.path.join(config.output_dir, 'opening_network_position.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig6)
            
            # Game dynamics visualization
            if 'game_dynamics' in results:
                fig8 = visualizer.visualize_game_dynamics(results['game_dynamics'])
                visualizer.save_visualization(
                    fig8,
                    os.path.join(config.output_dir, 'game_dynamics.png'),
                    dpi=config.dpi
                )
                if config.show:
                    visualizer.show_visualization(fig8)
            print("Visualizations saved to output directory")
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
