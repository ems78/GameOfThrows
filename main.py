#!/usr/bin/env python3
import os
import argparse
from src.modules.visualization.network_visualization import BlunderNetworkVisualization
from src.modules.analysis.blunder_graph_analysis import BlunderGraphAnalysis

def parse_args():
    parser = argparse.ArgumentParser(description='Generate chess blunder network visualizations')
    
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory to save visualizations (default: output)')
    
    parser.add_argument('--min-edge-weight', type=int, default=2,
                        help='Minimum edge weight for player blunder graph (default: 2)')
    
    parser.add_argument('--min-community-size', type=int, default=3,
                        help='Minimum size of communities to visualize (default: 3)')
    
    parser.add_argument('--top-openings', type=int, default=10,
                        help='Number of top openings to show (default: 10)')
    
    parser.add_argument('--dpi', type=int, default=300,
                        help='DPI for saved images (default: 300)')
    
    parser.add_argument('--show', action='store_true',
                        help='Show visualizations instead of saving them')
    
    parser.add_argument('-v', '--visualizations', type=str, nargs='+', 
                        default=['player', 'community', 'opening', 'weighted', 'rating'],
                        choices=['player', 'community', 'opening', 'weighted', 'rating', 'all'],
                        help='Which visualizations to generate (default: all)')
    
    parser.add_argument('--analyze', action='store_true',
                        help='Run the weighted blunder graph analysis')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not args.show:
        os.makedirs(args.output_dir, exist_ok=True)
    
    visualizer = BlunderNetworkVisualization()
    
    if args.analyze:
        print("Running weighted blunder graph analysis...")
        try:
            from src.modules.analysis.blunder_graph_analysis import run_analysis
            run_analysis()
        except Exception as e:
            print(f"Error running weighted blunder graph analysis: {str(e)}")
    
    vis_types = args.visualizations
    if 'all' in vis_types:
        vis_types = ['player', 'community', 'opening', 'weighted', 'rating']
    
    if 'player' in vis_types:
        print("Generating player blunder network visualization...")
        try:
            plt_obj = visualizer.visualize_player_blunder_graph(min_edge_weight=args.min_edge_weight)
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/player_blunder_network.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating player blunder network: {str(e)}")
    
    if 'community' in vis_types:
        print("Generating blunder communities visualization...")
        try:
            G = visualizer.analysis.create_player_blunder_graph()
            if len(G.nodes()) == 0:
                print("Warning: Player blunder graph is empty. Skipping community visualization.")
            else:
                plt_obj = visualizer.visualize_communities(min_community_size=args.min_community_size)
                if args.show:
                    visualizer.show_visualization(plt_obj)
                else:
                    visualizer.save_visualization(plt_obj, f'{args.output_dir}/blunder_communities.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating blunder communities: {str(e)}")
            print("You may need to install the python-louvain package: pip install python-louvain")
    
    if 'opening' in vis_types:
        print("Generating opening blunders visualization...")
        try:
            plt_obj = visualizer.visualize_opening_blunders(top_n=args.top_openings)
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/opening_blunders.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating opening blunders: {str(e)}")
    
    if 'weighted' in vis_types:
        print("Generating weighted blunder graph visualization...")
        try:
            plt_obj = visualizer.visualize_weighted_blunder_graph()
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/blunder_similarity_graph.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating weighted blunder graph: {str(e)}")
    
    if 'rating' in vis_types:
        print("Generating rating vs. blunder severity visualization...")
        try:
            plt_obj = visualizer.visualize_rating_vs_blunder_severity()
            if args.show:
                visualizer.show_visualization(plt_obj)
            else:
                visualizer.save_visualization(plt_obj, f'{args.output_dir}/rating_vs_blunder_severity.png', dpi=args.dpi)
        except Exception as e:
            print(f"Error generating rating vs. blunder severity visualization: {str(e)}")
    
    print("Visualization processing complete!")

if __name__ == "__main__":
    main()
