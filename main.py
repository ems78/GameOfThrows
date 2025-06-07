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
    if output_format == 'json':
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    elif output_format == 'csv':
        if isinstance(results, dict) and 'raw_data' in results:
            df = pd.DataFrame(results['raw_data'])
        else:
            df = pd.DataFrame([results])
        df.to_csv(filename, index=False)

def run_analysis(config: ChessAnalysisConfig) -> Dict[str, Any]:
    """Run network position analysis and return results."""
    analysis = Analysis()
    
    results = {
        'network_metrics': analysis.analyze_network_position_vs_winrate(),
        'opening_performance': analysis.analyze_opening_performance()
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
        print("Analyzing...")
        results = run_analysis(config)
        
        # Generate and save visualizations
        if results:
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
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
