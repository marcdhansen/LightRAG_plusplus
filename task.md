# Task: Implement Asymmetric Routing for ACE (lightrag-043)

- [x] **Define Configuration**: Update `LightRAG` and `QueryParam` to support `reflection_llm_model`. <!-- id: 0 -->
- [x] **Update Core ACE Loop**: Modify `lightrag.py` to route reflection and curation tasks to the `reflection_llm_model`. <!-- id: 1 -->
- [x] **Implement Model Threshold Check**: Add logic to warn or prevent using < 7B models for reflection if an alternative is available. <!-- id: 2 -->
- [x] **Test Routing**: Create a test script to verify that extraction uses the default model while reflection uses the specified specialist model. <!-- id: 3 -->
- [x] **Verify with Langfuse**: Ensure traces clearly show which model was used for which step. <!-- id: 4 -->
