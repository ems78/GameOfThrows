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
    
    try:
        # Import a small batch for testing (adjust as needed)
        # delete_all_data()
        print("Calling import_data_to_neo4j...")
        import_data_to_neo4j(batch_size=100, max_games=1000) # this will take some time because of Stockfish analysis
        print("Import process completed.")
    except Exception as e:
        print(f"Error during import: {str(e)}")
        import traceback
        traceback.print_exc()

