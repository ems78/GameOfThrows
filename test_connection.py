from src.modules.database.db_manager import Neo4jConnection

def test_connection():
    try:
        print("Attempting to connect to Neo4j...")
        db = Neo4jConnection()
        
        # Try a simple query
        result = db.query("RETURN 1 as test")
        print("Connection successful!")
        print(f"Test query result: {result}")
        
        db.close()
    except Exception as e:
        print(f"Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection() 
