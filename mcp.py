from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from utils import Neo4jConnection, semantic_search, add_embeddings_to_nodes
import uvicorn
import os

app = FastAPI(title="GraphRAG MCP Server")

class QueryRequest(BaseModel):
    query: str
    node_label: str
    top_k: int = 5

class GraphQuery(BaseModel):
    cypher: str
    parameters: Optional[Dict[str, Any]] = {}

class EmbeddingRequest(BaseModel):
    label: str
    text_property: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "GraphRAG MCP Server"}

@app.post("/search/semantic")
async def semantic_search_endpoint(request: QueryRequest):
    """Semantic search across graph nodes."""
    try:
        results = semantic_search(request.query, request.node_label, request.top_k)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/cypher")
async def execute_cypher(query: GraphQuery):
    """Execute custom Cypher query."""
    neo4j_conn = Neo4jConnection()
    try:
        with neo4j_conn.get_session() as session:
            result = session.run(query.cypher, query.parameters)
            records = [dict(record) for record in result]
            return {"results": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/generate")
async def generate_embeddings(request: EmbeddingRequest):
    """Generate and store embeddings for nodes."""
    try:
        add_embeddings_to_nodes(request.label, request.text_property)
        return {"status": "success", "message": f"Embeddings added to {request.label} nodes"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/schema")
async def get_schema():
    """Get graph schema."""
    neo4j_conn = Neo4jConnection()
    with neo4j_conn.get_session() as session:
        result = session.run("CALL db.schema.visualization()")
        return {"schema": [dict(record) for record in result]}

if __name__ == "__main__":
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", 8000))
    uvicorn.run(app, host=host, port=port)