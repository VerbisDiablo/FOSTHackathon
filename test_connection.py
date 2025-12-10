#!/usr/bin/env python3
"""
Diagnostic script to test Neo4j Aura connection
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import ssl
import time

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE", "neo4j")

print(f"Testing connection to: {uri}")
print(f"Database: {database}")
print()

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
