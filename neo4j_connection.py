"""
Minimal Neo4j connection utility for the mcp-neo4j-cypher server.
"""
import ssl
import os
from typing import Optional
from neo4j import GraphDatabase, TRUST_ALL_CERTIFICATES
from dotenv import load_dotenv

# Load .env with override to replace system environment variables
load_dotenv(override=True)


class Neo4jConnection:
    """Simple Neo4j connection manager."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            uri = os.getenv("NEO4J_URI")
            username = os.getenv("NEO4J_USER")
            password = os.getenv("NEO4J_PASSWORD")
            database = os.getenv("NEO4J_DATABASE", "neo4j")

            if not all([uri, username, password]):
                raise ValueError("Missing Neo4j credentials in .env file")

            # Create SSL context that ignores certificate verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            try:
                cls._instance.driver = GraphDatabase.driver(
                    uri, 
                    auth=(username, password),
                    encrypted=True,
                    trust=TRUST_ALL_CERTIFICATES,
                    ssl_context=ssl_context,
                    connection_timeout=60,
                    connection_acquisition_timeout=60
                )
                cls._instance.database = database
                cls._instance.uri = uri
                
                print(f"✓ Neo4j driver created: {uri}")
                print(f"✓ Database: {database}")
                    
            except Exception as e:
                raise ConnectionError(f"Failed to create Neo4j driver: {e}")
        
        return cls._instance

    def get_session(self, database: Optional[str] = None):
        """Get a new session."""
        db = database or self.database
        return self.driver.session(database=db)

    def close(self):
        """Close the driver."""
        if self.driver:
            self.driver.close()


def test_connection():
    """Test the Neo4j connection."""
    try:
        conn = Neo4jConnection()
        session = conn.get_session()
        
        # Get database stats
        result = session.run("MATCH (n) RETURN count(n) as nodes")
        nodes = result.single()["nodes"]
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as rels")
        rels = result.single()["rels"]
        
        session.close()
        
        print(f"✓ Database contains {nodes} nodes and {rels} relationships")
        return True
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
