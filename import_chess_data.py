import sys
import time
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.database.queries import import_data_to_neo4j, delete_all_data

print("Waiting for Neo4j to start...")
time.sleep(5) 

if __name__ == "__main__":
    print("Starting chess data import...")
    
    # Import a small batch for testing (adjust as needed)
    delete_all_data()
    import_data_to_neo4j(batch_size=2, max_games=10)
    
    # To import all data, use:
    # import_data_to_neo4j()
    
    print("Import process completed.") 
