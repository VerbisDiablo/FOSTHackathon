import sqlite3
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from typing import Dict, List, Any

load_dotenv()

class Neo4jMigrator:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

        # Get credentials from environment
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        print("Connecting to Neo4j...")
        print(f"URI: {uri}, USER: {username}")
        # Validate environment variables
        if not all([uri, username, password]):
            raise ValueError("Missing Neo4j credentials in .env file")

        # Create driver and verify connectivity
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        try:
            self.driver.verify_connectivity()
            print(f"✓ Successfully connected to Neo4j at {uri}")
        except Exception as e:
            self.driver.close()
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")

    def close(self):
        self.driver.close()

    def get_sqlite_tables(self) -> List[str]:
        """Get all table names from SQLite database."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get column information for a table."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        conn.close()
        return schema

    def migrate_table_to_nodes(self, table_name: str):
        """Migrate a SQLite table to Neo4j nodes."""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        with self.driver.session() as session:
            for row in rows:
                properties = dict(row)
                # Create node with table name as label
                session.run(
                    f"CREATE (n:{table_name} $properties)",
                    properties=properties
                )

        conn.close()
        print(f"Migrated {len(rows)} rows from {table_name} to Neo4j")

    def create_relationships(self, foreign_keys: List[Dict]):
        """Create relationships based on foreign key constraints."""
        with self.driver.session() as session:
            for fk in foreign_keys:
                query = f"""
                MATCH (a:{fk['from_table']})
                MATCH (b:{fk['to_table']})
                WHERE a.{fk['from_column']} = b.{fk['to_column']}
                CREATE (a)-[:{fk['relationship_name']}]->(b)
                """
                session.run(query)

    def migrate_all(self):
        """Migrate all tables from SQLite to Neo4j."""
        tables = self.get_sqlite_tables()
        print(f"Found tables: {tables}")

        for table in tables:
            print(f"Migrating {table}...")
            self.migrate_table_to_nodes(table)

        print("Migration complete!")

if __name__ == "__main__":
    # Replace with your .db file path
    migrator = Neo4jMigrator("DocGen_LLM.db")
    migrator.migrate_all()
    migrator.close()