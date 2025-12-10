# Neo4j GraphRAG MCP Setup

This repository contains the configuration for connecting to a Neo4j Aura database and using the mcp-neo4j-cypher MCP (Model Context Protocol) server.

## Prerequisites

- Python 3.8+
- Neo4j Aura instance with credentials

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your Neo4j Aura credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```dotenv
NEO4J_URI=bolt://YOUR_INSTANCE.databases.neo4j.io:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=YOUR_PASSWORD
NEO4J_DATABASE=neo4j
```

### 3. Test Connection

```bash
python neo4j_connection.py
```

Expected output:
```
✓ Neo4j driver created: bolt://...
✓ Database: neo4j
✓ Database contains XXXX nodes and XXXX relationships
```

## Using mcp-neo4j-cypher

The mcp-neo4j-cypher server provides a Model Context Protocol interface for querying Neo4j:

```bash
pip install mcp-neo4j-cypher
```

Then configure Claude Desktop or your MCP client to use it with the connection from this repository.

## Database Connection Details

- **URI Type**: `bolt://` (direct connection, not routing)
- **SSL**: Enabled with certificate verification disabled for Aura compatibility
- **Authentication**: Username/password (from .env)
- **Timeout**: 60 seconds (configurable in `neo4j_connection.py`)

## Troubleshooting

### Connection Issues

If you get "Unable to retrieve routing information", the bolt:// connection bypasses Neo4j clustering which is recommended for Aura instances.

If you get "Unauthorized due to authentication failure":
1. Check that NEO4J_PASSWORD in .env matches your Aura instance
2. Ensure no system environment variables are overriding .env (check `echo $NEO4J_PASSWORD`)

### Database Stats

Query your database:
```bash
python -c "from neo4j_connection import test_connection; test_connection()"
```

## Files

- `neo4j_connection.py` - Neo4j connection manager
- `.env.example` - Example configuration
- `.env` - Your actual credentials (not in git)
- `requirements.txt` - Python dependencies
