from neo4j import GraphDatabase
from src.config import NEO4J

class Neo4jConnection:
    def __init__(self, uri=NEO4J["uri"], user=NEO4J["user"], password=NEO4J["password"]):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()
        
    def query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]
            
    def init_schema(self):
        """Initialize database schema from schema.cypher file"""
        with open('src/modules/database/schema.cypher', 'r') as file:
            schema_queries = file.read().split(';')
            with self._driver.session() as session:
                for query in schema_queries:
                    if query.strip():
                        session.run(query)
