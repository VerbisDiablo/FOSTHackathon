#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files from the repository.
Run this to clean up the FOSTHackathon directory.
"""
import os
from pathlib import Path

# Files to KEEP
KEEP_FILES = {
    '.env',
    '.env.example',
    '.gitignore',
    'neo4j_connection.py',  # Our clean connection module
    'README.md',             # Documentation
    'requirements.txt',      # Dependencies
}

# Files/directories to REMOVE (cleanup)
REMOVE_PATTERNS = {
    'mcp.py',                # Old MCP server (use mcp-neo4j-cypher instead)
    'migration_script.py',   # Old script
    'utils.py',              # Old utilities (use neo4j_connection.py)
    'test_bolt.py',          # Test files
    'test_connection.py',
    'test_direct.py',
    'test_ssl.py',
    'templates/',            # Old web UI (use mcp-neo4j-cypher instead)
    '__pycache__/',
    '*.db',                  # Database files
}

def cleanup():
    """Remove unnecessary files."""
    repo_path = Path(__file__).parent
    
    print("Files to REMOVE:")
    print("-" * 50)
    
    removed = []
    for pattern in REMOVE_PATTERNS:
        if pattern.endswith('/'):
            # Directory
            dir_path = repo_path / pattern.rstrip('/')
            if dir_path.exists():
                import shutil
                shutil.rmtree(dir_path)
                print(f"  ✓ Removed directory: {pattern}")
                removed.append(pattern)
        elif '*' in pattern:
            # Glob pattern
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    print(f"  ✓ Removed file: {file_path.name}")
                    removed.append(file_path.name)
        else:
            # Single file
            file_path = repo_path / pattern
            if file_path.exists():
                file_path.unlink()
                print(f"  ✓ Removed file: {pattern}")
                removed.append(pattern)
    
    print("\n" + "=" * 50)
    print(f"Total files removed: {len(removed)}")
    
    print("\n" + "=" * 50)
    print("Repository structure after cleanup:")
    print("-" * 50)
    
    for file_path in sorted(repo_path.glob('*')):
        if file_path.name.startswith('.'):
            continue
        if file_path.is_file():
            print(f"  📄 {file_path.name}")
        elif file_path.is_dir():
            print(f"  📁 {file_path.name}/")

if __name__ == "__main__":
    import sys
    
    print("Neo4j Repository Cleanup")
    print("=" * 50)
    print("\nThis will remove old test files and use the clean neo4j_connection.py\n")
    
    response = input("Continue with cleanup? (yes/no): ")
    if response.lower() == 'yes':
        cleanup()
        print("\n✓ Cleanup complete!")
    else:
        print("Cleanup cancelled.")
        sys.exit(0)
