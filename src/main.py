def run_analysis():
    """Run all analysis methods and generate visualizations."""
    analysis = Analysis()
    visualization = Visualization()
    
    # Dictionary to store all analysis results
    results = {}
    
    # Run each analysis method
    print("Running network position vs winrate analysis...")
    results['network_position'] = analysis.analyze_network_position_vs_winrate()
    
    print("Running opening performance analysis...")
    results['opening_performance'] = analysis.analyze_opening_performance()
    
    print("Running gateway openings analysis...")
    results['gateway_openings'] = analysis.analyze_gateway_openings()
    
    print("Running opening communities analysis...")
    results['opening_communities'] = analysis.analyze_opening_communities()
    
    print("Running rating progression analysis...")
    results['rating_progression'] = analysis.analyze_rating_progression_by_opponent_rating()
    
    print("Running opening network position analysis...")
    results['opening_network'] = analysis.analyze_opening_network_position()
    
    print("Running player network characteristics analysis...")
    results['player_network'] = analysis.analyze_player_network_characteristics()
    
    print("Running game dynamics analysis...")
    results['game_dynamics'] = analysis.analyze_network_position_vs_game_dynamics()
    
    # Generate visualizations for each analysis result
    if results['network_position']:
        print("Generating network position visualization...")
        fig = visualization.visualize_network_metrics(results['network_position'])
        visualization.save_visualization(fig, 'output/network_position.png')
    
    if results['opening_performance']:
        print("Generating opening performance visualization...")
        fig = visualization.visualize_opening_performance(results['opening_performance'])
        visualization.save_visualization(fig, 'output/opening_performance.png')
    
    if results['gateway_openings']:
        print("Generating gateway openings visualization...")
        fig = visualization.visualize_gateway_openings(results['gateway_openings'])
        visualization.save_visualization(fig, 'output/gateway_openings.png')
    
    if results['opening_communities']:
        print("Generating opening communities visualization...")
        fig = visualization.visualize_opening_communities(results['opening_communities'])
        visualization.save_visualization(fig, 'output/opening_communities.png')
    
    if results['rating_progression']:
        print("Generating rating progression visualization...")
        fig = visualization.visualize_rating_progression(results['rating_progression'])
        visualization.save_visualization(fig, 'output/rating_progression.png')
    
    if results['opening_network']:
        print("Generating opening network metrics visualization...")
        fig = visualization.visualize_opening_network_metrics(results['opening_network'])
        visualization.save_visualization(fig, 'output/opening_network_metrics.png')
    
    if results['player_network']:
        print("Generating player network characteristics visualization...")
        fig = visualization.visualize_player_network_characteristics(results['player_network'])
        visualization.save_visualization(fig, 'output/player_network_characteristics.png')
    
    if results['game_dynamics']:
        print("Generating game dynamics visualization...")
        fig = visualization.visualize_game_dynamics(results['game_dynamics'])
        visualization.save_visualization(fig, 'output/game_dynamics.png')
    
    print("Analysis complete!") 
