#!/usr/bin/env python3
"""
Chess Network Analysis Tool

This script provides functionality for analyzing chess games, including data import,
network analysis, and visualization generation. It implements various research questions
related to temporal network evolution, player performance, opening theory, and game dynamics.
"""

import os
import argparse
import json
from typing import Dict, Any, List, Optional
import pandas as pd

from src.modules.database.import_data import import_data_to_neo4j, delete_all_data
from src.modules.database.queries import GraphQueries
from src.modules.visualization.network_visualization import NetworkVisualization
from src.modules.visualization.player_analysis_visualization import PlayerAnalysisVisualization
from src.modules.visualization.temporal_analysis_visualization import TemporalAnalysisVisualization
from src.modules.visualization.player_performance_visualization import PlayerPerformanceVisualization
from src.modules.visualization.game_ending_visualization import GameEndingVisualization
from src.modules.analysis.player_network_analysis import PlayerNetworkAnalysis
from src.modules.analysis.game_ending_analysis import GameEndingAnalysis
# from src.modules.analysis.temporal_analysis import TemporalAnalysis
# from src.modules.analysis.opening_analysis import OpeningAnalysis
# from src.modules.analysis.game_dynamics_analysis import GameDynamicsAnalysis
# from src.modules.visualization.opening_visualization import OpeningVisualization
# from src.modules.visualization.game_dynamics_visualization import GameDynamicsVisualization


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
        self.time_window = args.time_window
        self.top_openings = args.top_openings
        
        # Analysis type flags
        self.analyze_temporal = args.analyze_temporal
        self.analyze_player = args.analyze_player
        self.analyze_rating_progression = args.analyze_rating_progression
        self.analyze_network_position = args.analyze_network_position
        self.analyze_time_controls = args.analyze_time_controls
        self.analyze_opening_trends = args.analyze_opening_trends
        self.analyze_game_endings = args.analyze_game_endings
        
        # Visualization settings
        self.visualizations = args.visualizations


def parse_args() -> argparse.Namespace:
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
                       help='Directory to save visualizations (default: output)')
    parser.add_argument('--output-format', type=str, default='json',
                       choices=['json', 'csv'],
                       help='Output format for analysis results (default: json)')
    parser.add_argument('--dpi', type=int, default=300,
                       help='DPI for saved images (default: 300)')
    parser.add_argument('--show', action='store_true',
                       help='Show visualizations instead of saving them')
    
    # Analysis type arguments
    parser.add_argument('--analyze-temporal', action='store_true',
                       help='Analyze temporal network evolution')
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
    parser.add_argument('--analyze-game-endings', action='store_true',
                       help='Analyze patterns in how games end based on network metrics')
    
    # Analysis parameters
    parser.add_argument('--time-window', type=str, default='monthly',
                       choices=['daily', 'weekly', 'monthly', 'yearly'],
                       help='Time window for temporal analysis (default: monthly)')
    parser.add_argument('--top-openings', type=int, default=10,
                       help='Number of top openings to show (default: 10)')
    
    # Visualization types
    parser.add_argument('-v', '--visualizations', type=str, nargs='+', 
                       default=['temporal', 'opening', 'player', 'community', 'performance'],
                       choices=['temporal', 'opening', 'player', 'community', 'performance', 'all'],
                       help='Which visualizations to generate (default: all)')
    
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


def run_temporal_analysis(config: ChessAnalysisConfig) -> Dict:
    """
    Run temporal network evolution analysis.
    
    Args:
        config: Configuration object containing analysis parameters
        
    Returns:
        Dict containing temporal analysis results
    """
    print("Analyzing temporal network evolution...")
    queries = GraphQueries()
    results = queries.get_temporal_network_evolution(time_window=config.time_window)
    return results


def run_player_analysis(config: ChessAnalysisConfig) -> Dict:
    """
    Run player-specific analysis.
    
    Args:
        config: Configuration object containing analysis parameters
        
    Returns:
        Dict containing player analysis results
    """
    if not config.analyze_player:
        return None
        
    print(f"Analyzing player: {config.analyze_player}")
    player_analysis = PlayerNetworkAnalysis()
    results = player_analysis.predict_rating_progression(config.analyze_player)
    return results


def run_rating_progression_analysis(config: ChessAnalysisConfig) -> Dict:
    """
    Run rating progression analysis.
    
    Args:
        config: Configuration object containing analysis parameters
        
    Returns:
        Dict containing rating progression results
    """
    print("Analyzing rating progression...")
    player_analysis = PlayerNetworkAnalysis()
    results = player_analysis.analyze_rating_progression_by_opponent_rating()
    return results


def run_network_position_analysis(config: ChessAnalysisConfig) -> Dict:
    """
    Run network position analysis.
    
    Args:
        config: Configuration object containing analysis parameters
        
    Returns:
        Dict containing network position results
    """
    print("Analyzing network position...")
    player_analysis = PlayerNetworkAnalysis()
    results = player_analysis.analyze_network_position_vs_winrate()
    return results


def run_game_ending_analysis(config: ChessAnalysisConfig) -> Dict:
    """
    Run game ending analysis.
    
    Args:
        config: Configuration object containing analysis parameters
        
    Returns:
        Dict containing game ending results
    """
    print("Analyzing game endings...")
    game_ending_analysis = GameEndingAnalysis()
    results = game_ending_analysis.analyze_ending_patterns()
    return results


def main() -> None:
    """Main entry point for the application."""
    args = parse_args()
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
    
    # Initialize visualization classes
    network_viz = NetworkVisualization()
    player_viz = PlayerAnalysisVisualization()
    temporal_viz = TemporalAnalysisVisualization()
    performance_viz = PlayerPerformanceVisualization()
    game_ending_viz = GameEndingVisualization()
    
    # Run analyses and generate visualizations
    if config.analyze_temporal:
        print("Running temporal analysis...")
        results = run_temporal_analysis(config)
        if results:
            fig = temporal_viz.visualize_temporal_evolution(results, time_window=config.time_window)
            temporal_viz.save_visualization(
                fig,
                os.path.join(config.output_dir, 'temporal_analysis.png'),
                dpi=config.dpi
            )
            if config.show:
                temporal_viz.show_visualization(fig)
    
    if config.analyze_player:
        print(f"Analyzing player: {config.analyze_player}")
        results = run_player_analysis(config)
        if results:
            fig = player_viz.visualize_player_analysis(results)
            player_viz.save_visualization(
                fig,
                os.path.join(config.output_dir, f'player_analysis_{config.analyze_player}.png'),
                dpi=config.dpi
            )
            if config.show:
                player_viz.show_visualization(fig)
    
    if config.analyze_rating_progression:
        print("Analyzing rating progression...")
        results = run_rating_progression_analysis(config)
        if results:
            fig = performance_viz.visualize_rating_progression(results)
            performance_viz.save_visualization(
                fig,
                os.path.join(config.output_dir, 'rating_progression.png'),
                dpi=config.dpi
            )
            if config.show:
                performance_viz.show_visualization(fig)
    
    if config.analyze_network_position:
        print("Analyzing network position...")
        results = run_network_position_analysis(config)
        if results:
            fig = network_viz.visualize_network_metrics(results)
            network_viz.save_visualization(
                fig,
                os.path.join(config.output_dir, 'network_position.png'),
                dpi=config.dpi
            )
            if config.show:
                network_viz.show_visualization(fig)
    
    if config.analyze_game_endings:
        print("Analyzing game endings...")
        results = run_game_ending_analysis(config)
        if results:
            fig = game_ending_viz.visualize_ending_patterns(results)
            game_ending_viz.save_visualization(
                fig,
                os.path.join(config.output_dir, 'game_ending_analysis.png'),
                dpi=config.dpi
            )
            if config.show:
                game_ending_viz.show_visualization(fig)
    
    print("Analysis complete!")


if __name__ == "__main__":
    main()
