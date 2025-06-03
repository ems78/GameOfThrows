from src.modules.database.db_manager import Neo4jConnection
class GraphQueries:
    def __init__(self):
        self.db = Neo4jConnection()

    def get_temporal_network(self, time_window='monthly'):
        """
        Get player interactions over time.
        Returns a network of players who played against each other.
        """
        query = """
        MATCH (p1:Player)-[r1:PLAYED_IN]->(g:Game)<-[r2:PLAYED_IN]-(p2:Player)
        WHERE p1 <> p2
        WITH p1, p2, g,
             count(g) as games_played,
             collect({
                 game_id: g.id,
                 winner: g.winner,
                 turns: g.turns
             }) as game_details
        RETURN p1.username as player1, 
               p2.username as player2, 
               games_played,
               game_details
        ORDER BY games_played DESC
        """
        return self.db.query(query)

    def get_opening_network(self):
        """
        Get network of openings based on player usage.
        Returns openings and how they're used by players.
        """
        query = """
        MATCH (p:Player)-[:PLAYED_IN]->(g:Game)-[:USES]->(o:Opening)
        WITH o, p, count(g) as games_played
        WITH o, collect({
            player: p.username,
            games: games_played
        }) as player_usage
        RETURN o.eco_code, o.name, o.ply, player_usage
        ORDER BY size(player_usage) DESC
        """
        return self.db.query(query)

    def get_game_dynamics(self):
        """
        Get game dynamics including time controls, victory status, and game duration.
        """
        query = """
        MATCH (g:Game)
        WITH g.increment_code as time_control,
             g.victory_status as status,
             g.winner as winner,
             g.turns as turns
        RETURN 
            time_control,
            status,
            winner,
            count(*) as frequency,
            avg(turns) as avg_turns
        ORDER BY frequency DESC
        """
        return self.db.query(query)

    def get_temporal_network_evolution(self, time_window='monthly'):
        """
        Get network evolution data over time.
        Returns metrics about network growth, player activity, and opening trends.
        """
        query = """
        MATCH (g:Game)
        WITH g,
             datetime(g.created_at) as game_time,
             CASE
                 WHEN $time_window = 'daily' THEN date(game_time)
                 WHEN $time_window = 'weekly' THEN date(game_time - duration('P' + toString(dayofweek(game_time)-1) + 'D'))
                 WHEN $time_window = 'monthly' THEN date(game_time - duration('P' + toString(day(game_time)-1) + 'D'))
                 ELSE date(game_time - duration('P' + toString(dayofyear(game_time)-1) + 'D'))
             END as time_bucket
        WITH time_bucket,
             count(DISTINCT g) as total_games,
             count(DISTINCT [(p)-[:PLAYED_IN]->(g) | p]) as active_players,
             collect(DISTINCT g) as games
        WITH time_bucket, total_games, active_players, games,
             [(g in games)-[:USES]->(o) | o.eco_code] as openings_used
        RETURN time_bucket as timestamp,
               total_games,
               active_players,
               size(openings_used) as unique_openings,
               [opening in openings_used | {
                   code: opening,
                   count: size([x in openings_used WHERE x = opening])
               }] as opening_counts
        ORDER BY time_bucket
        """
        return self.db.query(query, time_window=time_window)

    def get_time_control_metrics(self):
        """
        Get metrics about how time controls affect game dynamics and network structure.
        """
        query = """
        MATCH (g:Game)
        WITH g.increment_code as time_control,
             g,
             duration.between(datetime(g.created_at), datetime(g.last_move_at)).seconds as game_duration
        WITH time_control,
             count(g) as total_games,
             avg(game_duration) as avg_duration,
             collect(g) as games
        WITH time_control, total_games, avg_duration, games,
             size([(p1)-[:PLAYED_IN]->(g)<-[:PLAYED_IN]-(p2) 
                  WHERE g in games AND p1 <> p2]) as total_connections,
             size([(p)-[:PLAYED_IN]->(g) WHERE g in games | p]) as total_players
        RETURN time_control,
               total_games,
               avg_duration as game_duration,
               toFloat(total_connections) / (total_players * (total_players - 1)) as network_density,
               [g in games | {
                   duration: duration.between(datetime(g.created_at), datetime(g.last_move_at)).seconds,
                   winner: g.winner,
                   victory_status: g.victory_status
               }] as game_details
        ORDER BY total_games DESC
        """
        return self.db.query(query)

    def get_opening_trends(self, time_window='monthly'):
        """
        Get trends in opening usage and their impact on game outcomes.
        """
        query = """
        MATCH (g:Game)-[:USES]->(o:Opening)
        WITH g, o,
             datetime(g.created_at) as game_time,
             CASE
                 WHEN $time_window = 'daily' THEN date(game_time)
                 WHEN $time_window = 'weekly' THEN date(game_time - duration('P' + toString(dayofweek(game_time)-1) + 'D'))
                 WHEN $time_window = 'monthly' THEN date(game_time - duration('P' + toString(day(game_time)-1) + 'D'))
                 ELSE date(game_time - duration('P' + toString(dayofyear(game_time)-1) + 'D'))
             END as time_bucket
        WITH time_bucket, o,
             count(g) as usage_count,
             sum(CASE WHEN g.winner = 'white' THEN 1 ELSE 0 END) as white_wins,
             sum(CASE WHEN g.winner = 'black' THEN 1 ELSE 0 END) as black_wins,
             sum(CASE WHEN g.winner = 'draw' THEN 1 ELSE 0 END) as draws
        RETURN time_bucket as timestamp,
               o.eco_code as opening,
               o.name as opening_name,
               usage_count,
               toFloat(white_wins) / usage_count as white_win_rate,
               toFloat(black_wins) / usage_count as black_win_rate,
               toFloat(draws) / usage_count as draw_rate
        ORDER BY time_bucket, usage_count DESC
        """
        return self.db.query(query, time_window=time_window)

    def get_player_network_metrics(self):
        """
        Get detailed network metrics for players including:
        - Centrality measures
        - Clustering coefficients
        - Rating progression
        - Win rates against similarly rated opponents
        """
        print("\n=== Player Network Metrics Query Debug ===")
        query = """
        MATCH (p:Player)-[r1:PLAYED_IN]->(g:Game)<-[r2:PLAYED_IN]-(opp:Player)
        WHERE p <> opp
        WITH p, opp, g, r1, r2,
             abs(toFloat(r1.rating_at_game) - toFloat(r2.rating_at_game)) as rating_diff
        WHERE rating_diff <= 100  // Only consider games against similarly rated opponents
        WITH p,
             count(g) as total_games,
             sum(CASE
                 WHEN g.winner = r1.color THEN 1
                 WHEN g.winner = 'draw' THEN 0.5
                 ELSE 0
             END) as wins,
             collect({
                 game_id: g.id,
                 rating: r1.rating_at_game,
                 opponent_rating: r2.rating_at_game,
                 result: CASE
                     WHEN g.winner = r1.color THEN 1
                     WHEN g.winner = 'draw' THEN 0.5
                     ELSE 0
                 END
             }) as game_history
        WHERE total_games >= 10
        RETURN 
            p.username as username,
            toFloat(p.rating) as current_rating,
            [x in game_history | x.rating][0] as initial_rating,
            [x in game_history | x.rating][-1] as latest_rating,
            toFloat(wins)/total_games as win_rate,
            total_games,
            game_history
        ORDER BY total_games DESC
        """
        print("Executing query...")
        results = self.db.query(query)
        print(f"Query returned {len(results)} records")
        # if len(results) > 0:
        #     print("\nFirst record sample:")
        #     print(results[0])
        #     print("\nRecord keys:")
        #     print(results[0].keys())
        return results

    def get_player_communities(self):
        """
        Get network structure for community detection.
        Returns player connections that can be used to detect communities.
        """
        query = """
        MATCH (p1:Player)-[:PLAYED_IN]->(g:Game)<-[:PLAYED_IN]-(p2:Player)
        WHERE p1 <> p2
        WITH p1, p2, count(g) as games_played
        RETURN p1.username as player1,
               p2.username as player2,
               games_played
        """
        return self.db.query(query)
