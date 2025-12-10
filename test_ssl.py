#!/usr/bin/env python3
"""
Test connection with different approaches
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import ssl
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

load_dotenv()

username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE", "neo4j")
original_uri = os.getenv("NEO4J_URI")
host = original_uri.replace("neo4j+s://", "").replace("neo4j://", "")

print("Testing with custom SSL context...")

try:
    # Create a custom SSL context that doesn't verify certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    uri = f"bolt+ssc://{host}:7687"
    print(f"URI: {uri}")
    
    driver = GraphDatabase.driver(uri, auth=(username, password), ssl_context=ssl_context)
    session = driver.session(database=database)
    
    print("Testing query...")
    result = session.run("RETURN 1 as test, date.today() as today")
    record = result.single()
    
    if record:
        print(f"✓ SUCCESS! Got result: {dict(record)}")
        print()
        print("✓ Connection works!")
        print(f"NEO4J_URI=bolt+ssc://{host}:7687")
    
    driver.close()
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
