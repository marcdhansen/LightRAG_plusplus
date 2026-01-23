from neo4j import GraphDatabase
import os
import sys

# Default Memgraph local connection
URI = "bolt://localhost:7687"
# Try default empty auth first, then memgraph/memgraph
AUTHS = [("", ""), ("memgraph", "memgraph")]

def check_vector_module():
    for auth in AUTHS:
        try:
            print(f"Attempting connection with auth: {auth}...")
            with GraphDatabase.driver(URI, auth=auth) as driver:
                driver.verify_connectivity()
                print("✅ Connected to Memgraph!")
                
                with driver.session() as session:
                    # Check for vector module by listing procedures
                    result = session.run("CALL mg.procedures() YIELD name RETURN name")
                    procedures = [record["name"] for record in result]
                    
                    vector_procs = [p for p in procedures if p.startswith("vector.")]
                    if vector_procs:
                        print(f"✅ Vector module FOUND! Detected {len(vector_procs)} vector procedures.")
                        print(f"Examples: {vector_procs[:5]}")
                        return True
                    else:
                        print("❌ Vector module NOT found.")
                        # Check what modules ARE loaded
                        modules = set([p.split(".")[0] for p in procedures])
                        print(f"Loaded modules: {sorted(list(modules))}")
                        return False
                        
        except Exception as e:
            print(f"Connection attempt failed: {e}")
    
    return False

if __name__ == "__main__":
    if check_vector_module():
        sys.exit(0)
    else:
        sys.exit(1)
