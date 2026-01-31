# State-of-the-Art (SOTA) Feature Roadmap

## 1. Vision
Transform LightRAG from a retrieval system into a **reasoning engine** that not only finds information but validates, explains, and evolves its understanding over time.

## 2. User Experience & Explainability

### 2.1 Semantic Highlighting
**Goal**: Ground answers visually in the source text.
- **Mechanism**:
    1.  LLM generates `<citation id="doc_1" span="10:50">text</citation>`.
    2.  UI parses spans and highlights corresponding text in the document viewer.
    3.  Hovering over citation highlights search result.

### 2.2 Progressive Disclosure
**Goal**: Reduce cognitive load while allowing deep dives.
- **Tiers**:
    - **L1 (Executive Summary)**: 2-sentence direct answer.
    - **L2 (Key Facts)**: Bullet points with source snippets.
    - **L3 (Source Dive)**: Full document context with graph relationships.
- **API Change**: Response object becomes hierarchical.

### 2.3 Chain-of-Thought (CoT) Visualization
**Goal**: Make the "Reasoning" visible.
- **Concept**:
    - Visualize the Knowledge Graph traversal path.
    - Show intermediate "thoughts" or "reasoning steps" (e.g., "Found entity 'Apple', checking 'Competitors'").
- **Implementation**:
    - Log graph traversal events.
    - Render as a flow/sequence diagram or animated graph in UI.

## 3. Memory & Continuity

### 3.1 Cross-Session Memory (`UserGraph`)
**Goal**: The system learns *about* the user.
- **Structure**: Separate Knowledge Graph for User Context.
- **Nodes**: `User`, `Preference`, `Project`, `Goal`.
- **Flow**:
    - Query: "Summarize this for my thesis."
    - UserKG: Knowing "Usage Context" = "Academic", adjusting tone.

### 3.2 Temporal Reasoning
**Goal**: Handle queries about change over time.
- **Mechanism**:
    - Timestamp edges in the Knowledge Graph.
    - Evaluation: "What changed in the Q3 report compared to Q2?"
    - Requires: Temporal-aware graph indices.

## 4. Technical Enablers
- **Streaming API**: Support real-time CoT updates.
- **Graph Visualization Lib**: Cytoscape.js or similar for frontend.
- **Vector + Graph Fusion**: Tighter coupling of vector similarity scores and graph centrality.
