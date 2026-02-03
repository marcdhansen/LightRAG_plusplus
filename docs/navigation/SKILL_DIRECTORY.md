# 🛠️ Complete Skills Directory

**Purpose**: Master index of all available agent capabilities with use cases and documentation links.

## 🌐 Global Skills (System-Wide)

### 🎯 Coordination & Management
**FlightDirector** (~/.gemini/antigravity/skills/FlightDirector/SKILL.md)
- **Purpose**: Project management, multi-agent coordination, strategic planning
- **Use for**: Complex project planning, coordinating multiple agents, strategic decisions
- **Commands**: `/flight-director`, project planning, task delegation

**Librarian** (~/.gemini/antigravity/skills/Librarian/SKILL.md)
- **Purpose**: Knowledge management, documentation organization, file cleanup
- **Use for**: Documentation reorganization, file cleanup, knowledge base management
- **Commands**: `/librarian`, knowledge organization, archival processes

**QualityAnalyst** (~/.gemini/antigravity/skills/QualityAnalyst/SKILL.md)
- **Purpose**: Code quality, testing strategy, best practices enforcement
- **Use for**: Code reviews, quality gates, testing strategy, standards compliance
- **Commands**: `/quality-analyst`, code reviews, quality assessments

**Reflect** (~/.gemini/antigravity/skills/Reflect/SKILL.md)
- **Purpose**: Learning from experience, process improvement, knowledge capture
- **Use for**: End-of-session reflections, learning capture, process optimization
- **Commands**: `/reflect`, learning capture, process analysis

### 💻 Technical Skills
**JavaScript** (~/.gemini/antigravity/skills/JavaScript/SKILL.md)
- **Purpose**: Frontend development, Node.js, web technologies
- **Use for**: Web UI development, JavaScript/TypeScript issues, frontend debugging
- **Commands**: `/javascript`, web development, frontend issues

**Coding Standards** (~/.gemini/antigravity/skills/coding-standards/SKILL.md)
- **Purpose**: Code style, best practices, consistency across languages
- **Use for**: Code style enforcement, consistency checks, coding standards
- **Commands**: `/coding-standards`, style guides, consistency checks

## 🏗️ Workspace Skills (LightRAG-Specific)

### 🧪 Testing & Quality
**Testing** (../../.agent/skills/testing/SKILL.md)
- **Purpose**: Test development, debugging, performance analysis
- **Use for**: Test failures, performance issues, test strategy, debugging
- **Commands**: `/testing`, test development, debugging, performance analysis

### 🎨 User Interface
**UI** (../../.agent/skills/ui/SKILL.md)
- **Purpose**: Web interface development, UI troubleshooting, frontend issues
- **Use for**: WebUI problems, frontend bugs, interface improvements, responsive design
- **Commands**: `/ui`, web interface development, frontend troubleshooting

### 🕸️ Knowledge Graph
**Graph** (../../.agent/skills/graph/SKILL.md)
- **Purpose**: Knowledge graph operations, entity extraction, graph optimization
- **Use for**: Graph database issues, entity extraction problems, graph queries
- **Commands**: `/graph`, knowledge graphs, entity extraction, graph optimization

### ⚙️ Operations & Process
**Process** (../../.agent/skills/process/SKILL.md)
- **Purpose**: Development workflows, automation, CI/CD, deployment
- **Use for**: Workflow automation, process improvements, deployment issues
- **Commands**: `/process`, workflows, automation, CI/CD

**Evaluation** (../../.agent/skills/evaluation/SKILL.md)
- **Purpose**: RAG evaluation, benchmarking, metrics analysis, performance testing
- **Use for**: Benchmarking, evaluation metrics, performance analysis, model comparison
- **Commands**: `/evaluation`, benchmarks, metrics, performance testing

**Docs** (../../.agent/skills/docs/SKILL.md)
- **Purpose**: Documentation creation, maintenance, knowledge base management
- **Use for**: Documentation writing, knowledge management, technical writing
- **Commands**: `/docs`, documentation creation, knowledge management

## 🎯 Skill Selection Guide

### **For Bug Fixes:**
- **UI issues** → [UI Skill](../../.agent/skills/ui/SKILL.md)
- **Test failures** → [Testing Skill](../../.agent/skills/testing/SKILL.md)
- **Graph problems** → [Graph Skill](../../.agent/skills/graph/SKILL.md)
- **Code quality** → [QualityAnalyst](~/.gemini/antigravity/skills/QualityAnalyst/SKILL.md)

### **For New Features:**
- **Frontend features** → [UI Skill](../../.agent/skills/ui/SKILL.md) + [JavaScript](~/.gemini/antigravity/skills/JavaScript/SKILL.md)
- **Backend features** → [Graph Skill](../../.agent/skills/graph/SKILL.md) + [Testing Skill](../../.agent/skills/testing/SKILL.md)
- **Process improvements** → [Process Skill](../../.agent/skills/process/SKILL.md)

### **For Project Management:**
- **Task coordination** → [FlightDirector](~/.gemini/antigravity/skills/FlightDirector/SKILL.md)
- **Documentation organization** → [Librarian](~/.gemini/antigravity/skills/Librarian/SKILL.md)
- **Quality assurance** → [QualityAnalyst](~/.gemini/antigravity/skills/QualityAnalyst/SKILL.md)

### **For Research & Analysis:**
- **Performance analysis** → [Evaluation Skill](../../.agent/skills/evaluation/SKILL.md)
- **Learning capture** → [Reflect](~/.gemini/antigravity/skills/Reflect/SKILL.md)
- **Knowledge organization** → [Librarian](~/.gemini/antigravity/skills/Librarian/SKILL.md)

## 🔧 Skill Usage Patterns

### **Common Combinations:**
1. **Feature Development**: UI + Graph + Testing + Docs
2. **Bug Investigation**: Testing + Graph + QualityAnalyst
3. **Process Improvement**: Process + QualityAnalyst + Reflect
4. **Documentation Project**: Librarian + Docs + Process

### **Workflow Integration:**
1. **Start**: FlightDirector for planning
2. **Execute**: Domain-specific skills (UI, Graph, etc.)
3. **Quality**: Testing + QualityAnalyst for validation
4. **Document**: Docs skill for knowledge capture
5. **Reflect**: Reflect skill for learning

### **Multi-Agent Coordination:**
1. **Session Management**: Always start with [agent-start.sh](../../.agent/scripts/agent-start.sh)
2. **Skill Coordination**: Use FlightDirector for complex multi-skill tasks
3. **Conflict Resolution**: QualityAnalyst for standards, Librarian for knowledge
4. **Knowledge Transfer**: Reflect + Docs for learning capture

## 📋 Skill Maintenance

**Adding New Skills:**
1. Create skill file in appropriate directory
2. Update this directory
3. Update [Quick Skills Reference](../quick/SKILLS.md)
4. Test skill integration

**Updating Existing Skills:**
1. Update skill documentation
2. Test with relevant use cases
3. Update dependencies if needed
4. Coordinate with other agents

---

**💡 Pro Tip**: The Librarian skill is meta - it helps manage and organize all other skills and documentation. Use it when you're unsure where to start or how to organize information.
