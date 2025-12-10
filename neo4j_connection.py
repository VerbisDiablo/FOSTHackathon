"""
Simple Neo4j connection.
"""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv(override=True)

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_driver():
    """Get Neo4j driver."""
    return GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def run_query(query, params=None):
    """Run a Cypher query and return results."""
    driver = get_driver()
    with driver.session(database=DATABASE) as session:
        result = session.run(query, params or {})
        records = [record.data() for record in result]
    driver.close()
    return records


def test():
    """Quick test."""
    print(f"Connecting to: {URI}")
    print(f"Database: {DATABASE}")
    
    try:
        # Count nodes
        result = run_query("MATCH (n) RETURN count(n) as count")
        print(f"✓ Nodes: {result[0]['count']}")
        
        # Count relationships  
        result = run_query("MATCH ()-[r]->() RETURN count(r) as count")
        print(f"✓ Relationships: {result[0]['count']}")
        
        print("✓ Connection works!")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    test()
