"""
Simple Flask app for Neo4j visualization with graph algorithms.
"""
from flask import Flask, render_template, request, jsonify
from neo4j_connection import get_driver, DATABASE

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


def extract_graph_data(result):
    """Extract nodes and edges from a Neo4j result."""
    nodes = {}
    edges = []
    
    for record in result:
        for value in record.values():
            # Handle nodes
            if hasattr(value, 'labels'):
                node_id = value.element_id
                if node_id not in nodes:
                    props = dict(value)
                    nodes[node_id] = {
                        'id': node_id,
                        'label': props.get('name', props.get('title', str(list(value.labels)[0]))),
                        'labels': list(value.labels),
                        'properties': props
                    }
            
            # Handle relationships
            elif hasattr(value, 'type'):
                edges.append({
                    'from': value.start_node.element_id,
                    'to': value.end_node.element_id,
                    'label': value.type,
                    'properties': dict(value)
                })
                
                for node in [value.start_node, value.end_node]:
                    node_id = node.element_id
                    if node_id not in nodes:
                        props = dict(node)
                        nodes[node_id] = {
                            'id': node_id,
                            'label': props.get('name', props.get('title', 'Node')),
                            'labels': list(node.labels),
                            'properties': props
                        }
            
            # Handle paths
            elif hasattr(value, 'nodes'):
                for node in value.nodes:
                    node_id = node.element_id
                    if node_id not in nodes:
                        props = dict(node)
                        nodes[node_id] = {
                            'id': node_id,
                            'label': props.get('name', props.get('title', 'Node')),
                            'labels': list(node.labels),
                            'properties': props
                        }
                for rel in value.relationships:
                    edges.append({
                        'from': rel.start_node.element_id,
                        'to': rel.end_node.element_id,
                        'label': rel.type,
                        'properties': dict(rel)
                    })
    
    return nodes, edges


@app.route('/query', methods=['POST'])
def query():
    """Execute a Cypher query and return nodes/edges for visualization."""
    cypher = request.json.get('query', '')
    
    if not cypher.strip():
        return jsonify({'error': 'Empty query'}), 400
    
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            result = session.run(cypher)
            nodes, edges = extract_graph_data(result)
        
        driver.close()
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/degree', methods=['POST'])
def analyze_degree():
    """Calculate degree centrality for nodes."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            # Get nodes with their degree (in + out connections)
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as degree
                RETURN n, degree
                ORDER BY degree DESC
                LIMIT 100
            """)
            
            nodes = {}
            max_degree = 1
            
            for record in result:
                node = record['n']
                degree = record['degree']
                node_id = node.element_id
                props = dict(node)
                
                if degree > max_degree:
                    max_degree = degree
                
                nodes[node_id] = {
                    'id': node_id,
                    'label': props.get('name', props.get('title', 'Node')),
                    'labels': list(node.labels),
                    'properties': props,
                    'score': degree
                }
            
            # Get edges between these nodes
            node_ids = list(nodes.keys())
            result = session.run("""
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN r
            """, {'ids': node_ids})
            
            edges = []
            for record in result:
                rel = record['r']
                edges.append({
                    'from': rel.start_node.element_id,
                    'to': rel.end_node.element_id,
                    'label': rel.type
                })
        
        driver.close()
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges,
            'algorithm': 'degree',
            'maxScore': max_degree
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/pagerank', methods=['POST'])
def analyze_pagerank():
    """Simulate PageRank using iterative degree calculation."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            # Simple PageRank approximation: nodes with many incoming links from important nodes
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)<-[r]-(m)
                WITH n, count(DISTINCT m) as inDegree
                OPTIONAL MATCH (n)-[r2]->(o)
                WITH n, inDegree, count(DISTINCT o) as outDegree
                WITH n, inDegree, outDegree, 
                     toFloat(inDegree) / (CASE WHEN outDegree = 0 THEN 1 ELSE outDegree END) as ratio
                RETURN n, inDegree, outDegree, ratio
                ORDER BY inDegree DESC
                LIMIT 100
            """)
            
            nodes = {}
            max_score = 1
            
            for record in result:
                node = record['n']
                score = record['inDegree']
                node_id = node.element_id
                props = dict(node)
                
                if score > max_score:
                    max_score = score
                
                nodes[node_id] = {
                    'id': node_id,
                    'label': props.get('name', props.get('title', 'Node')),
                    'labels': list(node.labels),
                    'properties': props,
                    'score': score,
                    'inDegree': record['inDegree'],
                    'outDegree': record['outDegree']
                }
            
            # Get edges
            node_ids = list(nodes.keys())
            result = session.run("""
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN r
            """, {'ids': node_ids})
            
            edges = []
            for record in result:
                rel = record['r']
                edges.append({
                    'from': rel.start_node.element_id,
                    'to': rel.end_node.element_id,
                    'label': rel.type
                })
        
        driver.close()
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges,
            'algorithm': 'pagerank',
            'maxScore': max_score
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/communities', methods=['POST'])
def analyze_communities():
    """Detect communities using label propagation simulation."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            # Get all nodes and their connections
            result = session.run("""
                MATCH (n)-[r]->(m)
                RETURN n, r, m
                LIMIT 500
            """)
            
            nodes = {}
            edges = []
            adjacency = {}  # node_id -> [connected_node_ids]
            
            for record in result:
                n = record['n']
                m = record['m']
                rel = record['r']
                
                for node in [n, m]:
                    node_id = node.element_id
                    if node_id not in nodes:
                        props = dict(node)
                        nodes[node_id] = {
                            'id': node_id,
                            'label': props.get('name', props.get('title', 'Node')),
                            'labels': list(node.labels),
                            'properties': props
                        }
                        adjacency[node_id] = []
                
                n_id = n.element_id
                m_id = m.element_id
                adjacency[n_id].append(m_id)
                adjacency[m_id].append(n_id)
                
                edges.append({
                    'from': rel.start_node.element_id,
                    'to': rel.end_node.element_id,
                    'label': rel.type
                })
            
            # Simple community detection: assign communities based on node labels first
            # then refine by connectivity
            communities = {}
            community_id = 0
            
            # Initial assignment by label
            label_to_community = {}
            for node_id, node in nodes.items():
                primary_label = node['labels'][0] if node['labels'] else 'Unknown'
                if primary_label not in label_to_community:
                    label_to_community[primary_label] = community_id
                    community_id += 1
                communities[node_id] = label_to_community[primary_label]
            
            # Label propagation refinement (3 iterations)
            for _ in range(3):
                new_communities = {}
                for node_id in nodes:
                    if node_id in adjacency and adjacency[node_id]:
                        # Get most common community among neighbors
                        neighbor_communities = [communities.get(n, 0) for n in adjacency[node_id]]
                        if neighbor_communities:
                            new_communities[node_id] = max(set(neighbor_communities), 
                                                          key=neighbor_communities.count)
                        else:
                            new_communities[node_id] = communities[node_id]
                    else:
                        new_communities[node_id] = communities[node_id]
                communities = new_communities
            
            # Add community to nodes
            for node_id in nodes:
                nodes[node_id]['community'] = communities.get(node_id, 0)
                nodes[node_id]['score'] = communities.get(node_id, 0)
        
        driver.close()
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges,
            'algorithm': 'communities',
            'maxScore': max(communities.values()) if communities else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/betweenness', methods=['POST'])
def analyze_betweenness():
    """Approximate betweenness centrality - nodes that bridge communities."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            # Find nodes that connect different label types (bridge nodes)
            result = session.run("""
                MATCH (n)-[r]-(m)
                WITH n, collect(DISTINCT labels(m)[0]) as connectedLabels
                WITH n, size(connectedLabels) as labelDiversity,
                     connectedLabels
                RETURN n, labelDiversity, connectedLabels
                ORDER BY labelDiversity DESC
                LIMIT 100
            """)
            
            nodes = {}
            max_score = 1
            
            for record in result:
                node = record['n']
                score = record['labelDiversity']
                node_id = node.element_id
                props = dict(node)
                
                if score > max_score:
                    max_score = score
                
                nodes[node_id] = {
                    'id': node_id,
                    'label': props.get('name', props.get('title', 'Node')),
                    'labels': list(node.labels),
                    'properties': props,
                    'score': score,
                    'connectedLabels': record['connectedLabels']
                }
            
            # Get edges
            node_ids = list(nodes.keys())
            result = session.run("""
                MATCH (n)-[r]->(m)
                WHERE elementId(n) IN $ids AND elementId(m) IN $ids
                RETURN r
            """, {'ids': node_ids})
            
            edges = []
            for record in result:
                rel = record['r']
                edges.append({
                    'from': rel.start_node.element_id,
                    'to': rel.end_node.element_id,
                    'label': rel.type
                })
        
        driver.close()
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges,
            'algorithm': 'betweenness',
            'maxScore': max_score
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/labels', methods=['GET'])
def get_labels():
    """Get all node labels in the database."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            result = session.run("CALL db.labels()")
            labels = [record[0] for record in result]
        driver.close()
        return jsonify({'labels': labels})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/relationships', methods=['GET'])
def get_relationships():
    """Get all relationship types in the database."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            result = session.run("CALL db.relationshipTypes()")
            types = [record[0] for record in result]
        driver.close()
        return jsonify({'types': types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/schema', methods=['GET'])
def get_schema():
    """Get database schema information for AI context."""
    try:
        driver = get_driver()
        schema = {}
        
        with driver.session(database=DATABASE) as session:
            # Get labels
            result = session.run("CALL db.labels()")
            schema['labels'] = [record[0] for record in result]
            
            # Get relationship types
            result = session.run("CALL db.relationshipTypes()")
            schema['relationships'] = [record[0] for record in result]
            
            # Get property keys for SymbolModel
            result = session.run("""
                MATCH (n:SymbolModel) 
                WITH n LIMIT 1 
                RETURN keys(n) as props
            """)
            record = result.single()
            schema['symbolProperties'] = record['props'] if record else []
            
            # Get distinct kinds
            result = session.run("MATCH (n:SymbolModel) RETURN DISTINCT n.kind as kind")
            schema['kinds'] = [record['kind'] for record in result if record['kind']]
            
            # Sample data for context
            result = session.run("MATCH (n:SymbolModel) RETURN n.name as name LIMIT 5")
            schema['sampleNames'] = [record['name'] for record in result]
        
        driver.close()
        return jsonify(schema)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Chat with Ollama to help build Cypher queries."""
    import requests
    
    user_message = request.json.get('message', '')
    model = request.json.get('model', 'llama3.2')
    
    if not user_message.strip():
        return jsonify({'error': 'Empty message'}), 400
    
    try:
        # Get schema for context
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            result = session.run("CALL db.labels()")
            labels = [record[0] for record in result]
            
            result = session.run("CALL db.relationshipTypes()")
            relationships = [record[0] for record in result]
            
            result = session.run("MATCH (n:SymbolModel) RETURN DISTINCT n.kind as kind")
            kinds = [record['kind'] for record in result if record['kind']]
            
            result = session.run("""
                MATCH (n:SymbolModel) 
                WITH n LIMIT 1 
                RETURN keys(n) as props
            """)
            record = result.single()
            symbol_props = record['props'] if record else []
        driver.close()
        
        # Build system prompt with schema context
        system_prompt = f"""You are a Neo4j Cypher query assistant. Help users build Cypher queries for their graph database.

DATABASE SCHEMA:
- Node Labels: {', '.join(labels)}
- Relationship Types: {', '.join(relationships)}
- SymbolModel kinds: {', '.join(kinds)}
- SymbolModel properties: {', '.join(symbol_props)}

IMPORTANT RULES:
1. SymbolModel nodes have a 'kind' property (class, function, method)
2. Use WHERE n.kind = 'class' to filter by kind, NOT :Class label
3. FileModel contains SymbolModel via CONTAINS relationship
4. FolderModel contains FileModel via CONTAINS relationship
5. Symbols can have tags via HAS_TAG relationship to Tag nodes
6. The 'documentation' property contains JSON with summary, description, parameters, examples, etc.

EXAMPLE QUERIES:
- All classes: MATCH (n:SymbolModel) WHERE n.kind = 'class' RETURN n LIMIT 50
- All functions: MATCH (n:SymbolModel) WHERE n.kind = 'function' RETURN n LIMIT 50
- File structure: MATCH (f:FileModel)-[r:CONTAINS]->(s:SymbolModel) RETURN f,r,s LIMIT 50
- Search by name: MATCH (n:SymbolModel) WHERE n.name CONTAINS 'Server' RETURN n
- With documentation: MATCH (n:SymbolModel) WHERE n.documentation IS NOT NULL RETURN n LIMIT 30

Respond with a valid Cypher query. If explaining, keep it brief and include the query.
Always return visualization-friendly queries (RETURN nodes and relationships, not just properties)."""

        # Call Ollama API
        ollama_response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': user_message,
                'system': system_prompt,
                'stream': False
            },
            timeout=60
        )
        
        if ollama_response.status_code == 200:
            response_data = ollama_response.json()
            return jsonify({
                'response': response_data.get('response', ''),
                'model': model
            })
        else:
            return jsonify({'error': f'Ollama error: {ollama_response.status_code}'}), 500
            
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to Ollama. Make sure Ollama is running (ollama serve)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ai/models', methods=['GET'])
def get_ollama_models():
    """Get available Ollama models."""
    import requests
    
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return jsonify({'models': models})
        return jsonify({'models': []})
    except:
        return jsonify({'models': [], 'error': 'Ollama not available'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
