from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jConnection:
    """Singleton connection to Neo4j database."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            uri = os.getenv("NEO4J_URI")
            username = os.getenv("NEO4J_USER")
            password = os.getenv("NEO4J_PASSWORD")

            if not all([uri, username, password]):
                raise ValueError("Missing Neo4j credentials in .env file")

            cls._instance.driver = GraphDatabase.driver(uri, auth=(username, password))
            try:
                cls._instance.driver.verify_connectivity()
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Neo4j: {e}")
        return cls._instance

    def get_session(self):
        return self.driver.session()

    def close(self):
        self.driver.close()


class EmbeddingGenerator:
    """Generate embeddings for graph nodes."""
    def __init__(self):
        provider = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
        if provider == "sentence-transformers":
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.model = SentenceTransformer(model_name)

    def generate(self, text: str) -> List[float]:
        """Generate embedding for given text."""
        return self.model.encode(text).tolist()

    def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts).tolist()


def add_embeddings_to_nodes(label: str, text_property: str):
    """Add vector embeddings to existing nodes in Neo4j."""
    neo4j_conn = Neo4jConnection()
    embedder = EmbeddingGenerator()

    with neo4j_conn.get_session() as session:
        # Fetch nodes
        result = session.run(f"MATCH (n:{label}) RETURN n.{text_property} as text, id(n) as node_id")
        nodes = list(result)

        # Generate embeddings
        texts = [node['text'] for node in nodes if node['text']]
        embeddings = embedder.batch_generate(texts)

        # Update nodes with embeddings
        for i, node in enumerate(nodes):
            if node['text']:
                session.run(
                    f"""
                    MATCH (n:{label})
                    WHERE id(n) = $node_id
                    SET n.embedding = $embedding
                    """,
                    node_id=node['node_id'],
                    embedding=embeddings[i]
                )

    print(f"Added embeddings to {len(embeddings)} {label} nodes")


def semantic_search(query: str, label: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform semantic search on graph nodes."""
    embedder = EmbeddingGenerator()
    query_embedding = embedder.generate(query)

    neo4j_conn = Neo4jConnection()
    with neo4j_conn.get_session() as session:
        # This requires Neo4j vector index (create separately)
        result = session.run(
            f"""
            MATCH (n:{label})
            WHERE n.embedding IS NOT NULL
            WITH n, gds.similarity.cosine(n.embedding, $query_embedding) as similarity
            ORDER BY similarity DESC
            LIMIT $top_k
            RETURN n, similarity
            """,
            query_embedding=query_embedding,
            top_k=top_k
        )
        return [{"node": dict(record["n"]), "similarity": record["similarity"]}
                for record in result]