---
name: Quality Analyst
description: Standards for performance evaluation, benchmarking, speed-accuracy tradeoff analysis, and UI/E2E testing.
---

# 📊 Quality Analyst Skill

## Purpose

The Quality Analyst (QA) ensures that system improvements are not just effective, but efficient and robust. This skill focuses on the substantive quality of the code, emphasizing both the **Speed-Accuracy Tradeoff** for backend systems and **User Interface Integrity** for frontend interactions.

All QA activities follow the **Spec-Driven TDD Protocol** (see `GEMINI.md`) to ensure objective verification of quality gates.

## 📋 Benchmarking Protocol (Backend/RAG)

### 1. Mandatory Dual Metrics

Whenever a performance-enhancing feature is implemented (e.g., reranking, pre-filtering, caching), the evaluation **MUST** report:

- **Accuracy Metrics**: RAGAS scores, NDCG, Recall, etc.
- **Latency Metrics**: Wall-clock time, CPU/GPU processing overhead, tokens per second.

### 2. Tradeoff Analysis

Documentation (specifically `walkthrough.md` and feature docs) must include a "Speed vs. Accuracy" section that weighs the gain in quality against the cost in processing time.

### 3. Baseline Consistency

Always run the "Baseline" (no feature) and "Enhanced" scenarios on the same hardware/environment to ensure comparative validity.

## 🖥️ UI Integrity Protocol (Frontend/E2E)

### 1. Playwright Standard

All user-facing features that involve complex interactions (e.g., forms, dynamic graphs, authentication flows) **MUST** have an accompanying Playwright E2E test.

- **Location**: `lightrag_webui/tests/`
- **Config**: `lightrag_webui/playwright.config.ts`
- **Command**: `bunx playwright test`

### 2. Visual Verification

For high-risk UI components (charts, graph visualizations):

- Use `toBeVisible()` checks for key elements.
- Verify that interactions (clicks, hovers) trigger the expected modal/state changes.
- **Minimal Mode**: When testing components in isolation (like `GraphViewer` in a modal), ensure controls meant to be hidden are indeed not visible.

### 3. Debugging

When writing new tests, enable verbose logging in `test.beforeEach` to capture page errors and console logs:

```typescript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
page.on('pageerror', exception => console.log('PAGE ERROR:', exception));
```

## 🛠️ Verification Checklist

- [ ] Accuracy benchmarks completed (Backend).
- [ ] Latency/Speed benchmarks completed (Backend).
- [ ] Speed vs. Accuracy tradeoff documented.
- [ ] Playwright E2E tests passed for UI changes (Frontend).
- [ ] Optimal configuration recommended based on environment.
