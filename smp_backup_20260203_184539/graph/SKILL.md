# 🕸️ Graph Skill

**Purpose**: Manages knowledge graph operations for LightRAG, including visualization, curation, and analysis of entity-relationship structures.

## 🎯 Mission
- Visualize and inspect knowledge graphs
- Manage graph storage and indexing
- Curate and repair graph structures
- Analyze entity relationships and patterns

## 🛠️ Tools & Scripts

### Graph Visualization
```bash
# Visualize knowledge graph structure
python3 scripts/visualize_graph.py --format interactive

# Export graph for analysis
python3 scripts/export_graph.py --format cytoscape
```

### Graph Curation
```bash
# Clean and repair graph inconsistencies
python3 scripts/repair_graph.py --auto-fix

# Remove duplicate entities
python3 scripts/dedup_entities.py --threshold 0.95
```

### Graph Analysis
```bash
# Analyze graph density and connectivity
python3 scripts/analyze_graph.py --metrics all

# Find influential entities
python3 scripts/find_key_entities.py --centrality pagerank
```

### Storage Management
```bash
# Optimize graph storage
python3 scripts/optimize_storage.py --backend neo4j

# Rebuild graph indexes
python3 scripts/rebuild_indexes.py
```

## 📋 Usage Examples

### Basic Graph Operations
```bash
# Visualize current knowledge graph
/graph --visualize --full

# Check graph health
/graph --health-check

# Generate graph statistics
/graph --stats --detailed
```

### Entity Management
```bash
# Find related entities
/graph --find-related --entity "Albert Einstein"

# Merge duplicate entities
/graph --merge-duplicates --entity "Apple Inc"

# Add new entity relationships
/graph --add-relation --from "Person" --to "Organization" --type "works_for"
```

### Storage Operations
```bash
# Backup knowledge graph
/graph --backup --destination backups/

# Restore from backup
/graph --restore --source backups/graph_backup.json

# Migrate between storage backends
/graph --migrate --from neo4j --to memgraph
```

## 🔗 Integration Points
- **Extraction Skill**: Feed extracted entities into graph
- **Query Skill**: Retrieve graph-based answers
- **Evaluation Skill**: Evaluate graph quality and completeness
- **UI Skill**: Display graph visualizations in web interface

## 📊 Metrics Tracked
- Graph size and entity counts
- Relationship density and clustering
- Query performance on graph data
- Storage efficiency and indexing

## 🎯 Key Files
- `lightrag/kg/` - Knowledge graph implementations
- `scripts/visualize_graph.py` - Graph visualization
- `graphs/` - Graph data exports and backups
- Graph storage backends (Neo4j, Memgraph, etc.)
