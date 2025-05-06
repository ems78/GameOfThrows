import networkx as nx
from ..database.db_manager import Neo4jConnection

class BlunderCommunityAnalysis:
    """
    Analyzes blunder communities within the chess database.
    
    A blunder community is a group of players who make similar mistakes in similar positions.
    """
    
    def __init__(self):
        self.db = Neo4jConnection()
        
    def create_player_blunder_graph(self):
        """
        Creates a graph where players are connected if they made similar blunders.
        
        Returns:
            NetworkX graph with players as nodes and weighted edges representing shared blunders
        """
        # Query to find pairs of players who made similar blunders
        query = """
        MATCH (p1:Player)-[:MADE_BLUNDER]->(b1:Blunder)
        MATCH (p2:Player)-[:MADE_BLUNDER]->(b2:Blunder)
        WHERE p1 <> p2 
        AND b1.position_fen = b2.position_fen
        RETURN p1.id as player1, p2.id as player2, COUNT(DISTINCT b1) as shared_blunders
        """
        
        result = self.db.query(query)
        
        # Create graph
        G = nx.Graph()
        
        # Add edges with weights based on shared blunders
        for record in result:
            player1 = record['player1']
            player2 = record['player2']
            weight = record['shared_blunders']
            
            # Add nodes if they don't exist
            if not G.has_node(player1):
                G.add_node(player1)
            if not G.has_node(player2):
                G.add_node(player2)
                
            # Add or update edge weight
            if G.has_edge(player1, player2):
                G[player1][player2]['weight'] += weight
            else:
                G.add_edge(player1, player2, weight=weight)
                
        return G
    
    def detect_communities(self, min_community_size=3):
        """
        Detect communities of players who make similar blunders
        
        Args:
            min_community_size: Minimum number of players in a community
            
        Returns:
            List of communities (each community is a list of player IDs)
        """
        G = self.create_player_blunder_graph()
        
        # Check if graph is empty
        if len(G.nodes()) == 0:
            print("Warning: Player blunder graph is empty. No communities detected.")
            return []
            
        # Use Louvain method for community detection
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
            
            # Group players by community
            communities = {}
            for player, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(player)
                
            # Filter by minimum size
            return [comm for comm in communities.values() if len(comm) >= min_community_size]
        except ImportError:
            # Fallback to NetworkX community detection
            try:
                from networkx.algorithms import community
                
                # Check if graph has at least one edge
                if len(G.edges()) == 0:
                    print("Warning: Player blunder graph has no edges. Cannot detect communities.")
                    return []
                    
                communities = list(community.greedy_modularity_communities(G))
                return [list(comm) for comm in communities if len(comm) >= min_community_size]
            except ValueError as e:
                print(f"Community detection error: {str(e)}")
                print("This may be due to an empty or disconnected graph.")
                return []
            
    def analyze_blunder_patterns_in_community(self, community):
        """
        Analyze common blunder patterns within a community
        
        Args:
            community: List of player IDs in the community
            
        Returns:
            Dictionary with common blunder patterns
        """
        # Check if community is empty
        if not community:
            print("Warning: Empty community provided. Cannot analyze patterns.")
            return []
            
        # Join player IDs for Cypher query
        player_ids = "', '".join(community)
        
        # Query to find common blunders in the community
        query = f"""
        MATCH (p:Player)-[:MADE_BLUNDER]->(b:Blunder)
        WHERE p.id IN ['{player_ids}']
        WITH b.position_fen as position, count(DISTINCT p) as num_players
        WHERE num_players >= {len(community) // 2}
        RETURN position, num_players
        ORDER BY num_players DESC
        LIMIT 10
        """
        
        result = self.db.query(query)
        
        return [{
            'position': record['position'],
            'num_players': record['num_players'],
            'percentage': (record['num_players'] / len(community)) * 100
        } for record in result] 
