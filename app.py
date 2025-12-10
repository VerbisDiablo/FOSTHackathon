"""
Simple Flask app for Neo4j visualization.
"""
from flask import Flask, render_template, request, jsonify
from neo4j_connection import get_driver, DATABASE

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


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
                        
                        # Also add the connected nodes
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
        
        driver.close()
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/node/<path:node_id>')
def get_node(node_id):
    """Get full node details including documentation."""
    try:
        driver = get_driver()
        with driver.session(database=DATABASE) as session:
            result = session.run(
                "MATCH (n) WHERE elementId(n) = $id RETURN n",
                {'id': node_id}
            )
            record = result.single()
            
            if record:
                node = record['n']
                props = dict(node)
                driver.close()
                return jsonify({
                    'id': node.element_id,
                    'labels': list(node.labels),
                    'properties': props
                })
            
        driver.close()
        return jsonify({'error': 'Node not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
