#!/usr/bin/env python3
"""
Test direct bolt connections
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import time

load_dotenv()

username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE", "neo4j")

# Extract just the hostname from the URI
original_uri = os.getenv("NEO4J_URI")
host = original_uri.replace("neo4j+s://", "").replace("neo4j://", "")

# Try direct bolt+s connections
attempts = [
    {
        "name": "bolt+s (TLS secured bolt)",
        "uri": f"bolt+s://{host}:7687"
    },
    {
        "name": "Direct bolt+s to 7687",
        "uri": f"bolt+s://{host}"
    },
    {
        "name": "Direct bolt+s to 7473 (alt port)",
        "uri": f"bolt+s://{host}:7473"
    }
]

for attempt in attempts:
    try:
        uri = attempt["uri"]
        print(f"Attempt: {attempt['name']}")
        print(f"  URI: {uri}")
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        session = driver.session(database=database)
        
        print(f"  Testing query...")
        result = session.run("RETURN 1 as test")
        record = result.single()
        
        if record:
            print(f"  ✓ SUCCESS!")
            print()
            print(f"✓ Found working configuration!")
            print(f"NEO4J_URI={uri}")
            driver.close()
            break
        else:
            print(f"  ✗ No result")
            driver.close()
    except Exception as e:
        error_msg = str(e)[:150]
        print(f"  ✗ Error: {type(e).__name__}: {error_msg}")
    
    print()
    time.sleep(2)
