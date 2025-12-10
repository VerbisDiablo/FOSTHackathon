#!/usr/bin/env python3
"""
Diagnostic script to test Neo4j Aura connection
"""
import ssl
from neo4j import GraphDatabase, TRUST_ALL_CERTIFICATES

uri = "bolt://0e343e24.databases.neo4j.io:7687"
user = "neo4j"
password = "RE3TbZ7-Snmx0rn-OZ5KEgAwT7Twk8Mb6U64gE-JjQw"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

try:
    print(f"Connecting to {uri}...")
    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        encrypted=True,
        trust=TRUST_ALL_CERTIFICATES,
        ssl_context=ssl_context
    )
    
    with driver.session(database="neo4j") as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"✓ SUCCESS! Connected to database")
        print(f"✓ Total nodes: {count}")
        
        # Get relationship count
        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = rel_result.single()["count"]
        print(f"✓ Total relationships: {rel_count}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()



# Try different connection approaches
attempts = [
    {
        "name": "Standard connection",
        "config": {}
    },
    {
        "name": "With disabled hostname verification",
        "config": {
            "trust": "TRUST_ALL_CERTIFICATES"
        }
    },
    {
        "name": "With max pool size 1",
        "config": {
            "max_pool_size": 1
        }
    },
    {
        "name": "Bolt protocol (no encryption)",
        "uri": "bolt://" + uri.replace("neo4j+s://", ""),
        "config": {}
    }
]

for attempt in attempts:
    try:
        test_uri = attempt.get("uri", uri)
        config = attempt.get("config", {})
        print(f"Attempt: {attempt['name']}")
        print(f"  URI: {test_uri}")
        print(f"  Config: {config}")
        
        driver = GraphDatabase.driver(test_uri, auth=(username, password), **config)
        
        # Try to get a session
        session = driver.session(database=database)
        result = session.run("RETURN 1 as test")
        record = result.single()
        
        if record:
            print(f"  ✓ SUCCESS! Got result: {record}")
            print()
            print("Use this configuration in your .env file:")
            if config:
                for key, value in config.items():
                    print(f"  {key}={value}")
            driver.close()
            break
        else:
            print(f"  ✗ Failed - no result")
            driver.close()
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {str(e)[:100]}")
    
    print()
    time.sleep(2)
