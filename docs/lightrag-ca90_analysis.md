# lightrag-ca90 Feature Analysis: Terminology Standardization

## Overview

This document analyzes the comprehensive terminology standardization initiative to replace legacy "mission" terminology with "session" terminology across all LightRAG documentation, skills, and universal standards.

## Problem Statement

Legacy "mission" terminology is extensively used throughout the codebase but should be updated to "session" terminology to align with current Universal Agent Protocol. This creates confusion and inconsistency in documentation and skill references.

## Technical Requirements

### Core Components
1. **Universal Standards Update**: Update `~/.agent/docs/NOMENCLATURE.md` and `ONBOARDING.md`
2. **Phase Documents**: Update phase documents to reference current skill names
3. **Skill Descriptions**: Remove legacy mission references from skill files
4. **Project SOPs**: Update project-level documentation

### Files Requiring Updates
- `/Users/marchansen/.agent/docs/NOMENCLATURE.md` - Mission Nomenclature → Session Terminology
- `/Users/marchansen/.agent/docs/ONBOARDING.md` - SMP references
- `/Users/marchansen/.agent/docs/phases/01_session_context.md` - `/mission-briefing` skill reference
- `/Users/marchansen/.agent/docs/phases/06_retrospective.md` - `/mission-debriefing` skill reference
- `/Users/marchansen/.gemini/antigravity/skills/reflect/SKILL.md` - Legacy mission references
- `/Users/marchansen/.gemini/antigravity/skills/retrospective/SKILL.md` - Post-mission terminology
- `/Users/marchansen/.gemini/antigravity/skills/initialization-briefing/SKILL.md` - Pre-mission terminology

## Implementation Strategy

### Phase 1: Universal Standards (P0)
- [ ] Update `NOMENCLATURE.md` → `SESSION_TERMINOLOGY.md`
- [ ] Update `ONBOARDING.md` SMP references
- [ ] Standardize terminology mapping

### Phase 2: Skills Documentation (P1)
- [ ] Update skill descriptions to use "session" terminology
- [ ] Remove legacy "mission" references from skill files
- [ ] Ensure skill name consistency

### Phase 3: Project Documentation (P2)
- [ ] Update project-level SOP documents
- [ ] Update cross-references and links
- [ ] Validate all documentation integrity

## Terminology Mapping

| Legacy Term | Current Term | Context |
|-------------|--------------|---------|
| Mission | Session | Work session timeframe |
| Mission Briefing | Initialization Briefing | Pre-work preparation |
| Mission Debriefing | Retrospective | Post-work analysis |
| Pre-mission | Pre-session | Before work starts |
| Post-mission | Post-session | After work completes |
| SMP (Standard Mission Protocol) | Universal Agent Protocol | Complete workflow |

## Testing Strategy

### Validation Tests
- [ ] Legacy term identification in target files
- [ ] Session terminology replacement verification
- [ ] Skill name consistency validation
- [ ] Documentation integrity checks
- [ ] Cross-reference validation

### Quality Assurance
- [ ] Markdown duplicate detection
- [ ] Link validation
- [ ] Header structure verification
- [ ] Content completeness checks

## Success Criteria

### Functional Requirements
- [ ] 100% of legacy mission terms replaced with session terminology
- [ ] All skill references use current skill names
- [ ] Documentation maintains integrity after updates
- [ ] No broken cross-references or links

### Quality Requirements
- [ ] Zero duplicate markdown files
- [ ] All links and references functional
- [ ] Consistent terminology across all documentation
- [ ] Proper markdown structure maintained

## Risk Assessment

### Low Risk
- Documentation-only changes
- No code functionality impact
- Reversible changes

### Mitigation Strategies
- Branch isolation for changes
- Comprehensive testing before merge
- Step-by-step validation
- Rollback capability preserved

---

*Document Version: 1.0*
*Last Updated: 2026-02-06*
*Author: Marc Hansen*
*Task ID: lightrag-ca90*

---

*Document Version: 1.0*
*Last Updated: 2026-02-06*
*Author: Marc Hansen*
