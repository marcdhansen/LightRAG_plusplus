Hugging Face provides several frameworks and models suitable for creating a "router" or "master" LLM that delegates tasks to specialized, smaller models. This approach, often referred to as Agentic Task Delegation or the Delegated Chain of Thought (D-CoT) architecture, optimizes performance and reduces computational costs.
Here are the best options from Hugging Face for delegating work:
1. Top Recommended "Router" LLMs (The Controller)
These models are proficient at analyzing user input, breaking it down into subtasks, and choosing the right tool or model:
• Mistral-7B-Instruct / Mixtral-8x7B: Excellent for instruction following and reasoning tasks, making them ideal for determining which specialized model to call next.
• Meta Llama 3 (8B or 70B): Strong, versatile models capable of acting as a "manager" in a multi-agent system.
• Microsoft Phi-3-Mini: A highly efficient 3.8B parameter model suitable for on-device or fast, low-cost routing. [2, 9, 10, 11, 12]
2. Frameworks for Delegation
• Hugging Face Agents (Transformers Agents 2.0): This framework allows you to use a powerful LLM to manage a set of tools (functions) and other specialized models. It includes a "Code Agent" that can securely execute code-based tasks.
• Delegated Chain of Thought (D-CoT): A specific architectural approach supported by Hugging Face where a central "modulith" model handles reasoning and delegates execution tasks to specialized models.
• OpenAGI: A framework that integrates with Hugging Face models to build agentic workflows, featuring a for delegating work to specialized agents. [1, 5, 13, 14, 15]
3. Implementation Strategy
To build a delegation system on Hugging Face:
1. Define Specialized Workers: Use smaller, fine-tuned models for specific tasks (e.g., a BERT model for classification, a T5 model for translation, a specialized Llama 3 for code).
2. Set up the Router: Use a larger model (e.g., Mixtral) to analyze the query.
3. Implement Tool Use: Use the Transformers library to have the router call the appropriate model based on the query, as demonstrated in the "License to Call" approach. [1, 2, 13, 16, 17]
For example, a user query "Translate this technical document and summarize it" would be routed by the main agent to a Translation Model (e.g., NLLB) and then to a Summarization Model (e.g., BART). [2, 16, 18, 19, 20]
AI responses may include mistakes.
[1] https://huggingface.co/blog/Pier-Jean/delegated-chain-of-thought
[2] https://huggingface.co/blog/adarshxs/agentic-task-delegation
[3] https://blog.rewanthtammana.com/securing-your-data-with-local-ai-model-execution-a-guide-using-hugging-face
[4] https://www.komtas.com/en/glossary/hugging-face-nedir
[5] https://huggingface.co/blog/lucifertrj/openagi-blog
[6] https://docs.together.ai/docs/parallel-workflows
[7] https://www.domo.com/blog/how-to-choose-the-best-large-language-model-llm-for-each-and-every-task
[8] https://arxiv.org/pdf/2508.10016
[9] https://huggingface.co/blog/dvgodoy/fine-tuning-llm-hugging-face
[10] https://agentissue.medium.com/hugging-faces-unified-api-standardizing-tool-use-across-top-ai-models-from-mistral-cohere-nous-2210bdb4f2a7
[11] https://arxiv.org/html/2503.01464v1
[12] https://developers.redhat.com/articles/2024/06/17/experiment-and-test-ai-models-podman-ai-lab
[13] https://medium.com/data-science/multi-agentic-rag-with-hugging-face-code-agents-005822122930
[14] https://medium.com/@mojahid.iitdelhi/enhancing-the-performance-of-large-language-models-with-hugging-face-agents-ddb0b559dd94
[15] https://odsc.medium.com/the-evolution-of-hugging-face-and-its-role-in-democratizing-ai-76f19af6d374
[16] https://www.geeksforgeeks.org/deep-learning/how-to-fine-tune-an-llm-from-hugging-face/
[17] https://www.youtube.com/watch?v=zTQXu80GAxI
[18] https://www.researchgate.net/publication/379022971_NO_LANGUAGE_LEFT_BEHIND_NLLB-200_AI_TRANSLATION_MODEL_REVIEW
[19] https://arxiv.org/html/2502.19339v1
[20] https://www.ibm.com/architectures/hybrid/genai-document-summarization
