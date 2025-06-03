from src.modules.database.db_manager import Neo4jConnection
class GraphQueries:
    def __init__(self):
        self.db = Neo4jConnection()

    def get_temporal_network(self, time_window='monthly'):
        """
        Get player interactions over time windows.
        Returns a network of players who played against each other in each time window.
        """
        query = """
        MATCH (p1:Player)-[r1:PLAYED_IN]->(g:Game)<-[r2:PLAYED_IN]-(p2:Player)
        WHERE p1 <> p2
        WITH p1, p2, g, datetime(g.created_at) as game_time
        WITH p1, p2, 
             toString(datetime(game_time)) as time_window,
             count(g) as games_played,
             collect({
                 game_id: g.id,
                 winner: g.winner,
                 turns: g.turns
             }) as game_details
        RETURN p1.username as player1, p2.username as player2, 
               time_window, games_played, game_details
        ORDER BY time_window, games_played DESC
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

    def get_player_network_metrics(self):
        """
        Get network metrics for players including:
        - Number of games played
        - Rating progression
        - Win rate
        """
        query = """
        MATCH (p:Player)-[r:PLAYED_IN]->(g:Game)
        WITH p, 
             count(DISTINCT g) as games_played,
             collect({
                 game_id: g.id,
                 rating: r.rating_at_game,
                 color: r.color,
                 winner: g.winner
             }) as game_history
        RETURN 
            p.username,
            p.rating,
            games_played,
            [x in game_history | x.rating][0] as initial_rating,
            [x in game_history | x.rating][-1] as latest_rating,
            size([x in game_history WHERE (x.color = 'white' AND x.winner = 'white') OR 
                                           (x.color = 'black' AND x.winner = 'black')]) as wins
        ORDER BY games_played DESC
        """
        return self.db.query(query)

    def get_player_communities(self):
        """
        Get communities of players based on their game interactions.
        """
        query = """
        CALL gds.louvain.stream({
            nodeProjection: 'Player',
            relationshipProjection: {
                PLAYED_IN: {
                    type: 'PLAYED_IN',
                    orientation: 'UNDIRECTED'
                }
            }
        })
        YIELD nodeId, communityId
        RETURN gds.util.asNode(nodeId).username as player,
               communityId
        ORDER BY communityId, player
        """
        return self.db.query(query)
