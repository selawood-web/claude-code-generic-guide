# Making AI more efficient — platform & developer techniques (2026)

- **As of:** 2026-08-28
- **Staleness class:** mixed — the technique categories are stable; specific
  prices, discounts, model names, and framework benchmarks are volatile and
  should be re-verified before acting on them
- **Scope:** the newest widely-adopted ways AI platforms (Anthropic, OpenAI,
  Google) and developer platforms/serving stacks make AI cheaper, faster, and
  less token-hungry — from API-level features down to serving infrastructure

## Summary

Efficiency gains in 2026 come from four layers that stack multiplicatively:

1. **Platform API features** — prompt caching, batch APIs, model routing,
   adaptive reasoning/effort control. Stacked, these commonly cut bills 60–80%.
2. **Agent & context engineering** — compaction, subagent isolation, selective
   tool loading. Compression alone can cut agent token usage by ~50–80%.
3. **Model architecture** — small language models, mixture-of-experts,
   distillation: more intelligence per active parameter.
4. **Serving infrastructure** — quantization, speculative decoding, KV-cache
   optimization, disaggregated prefill/decode: 1.5–4x throughput per technique
   on the same hardware.

## 1. Platform-level features (highest leverage, least effort)

- **Prompt caching** — cached input reads cost ~10% of the normal input rate
  (a 90% discount). OpenAI activates it automatically from 1,024 tokens
  (30-minute retention from GPT-5.6 on; writes 1.25x input). Anthropic uses an
  explicit `cache_control` marker (reads 0.1x, writes 1.25x, 5-minute default
  TTL). Gemini enables implicit caching by default on 2.5+ but with no
  guaranteed discount. Structure prompts static-prefix-first to maximize hits.
- **Batch APIs** — both OpenAI and Anthropic offer ~50% off for asynchronous
  workloads with a longer SLA. Nearly free 2x discount for anything that can
  wait: overnight enrichment, embeddings backfill, offline analytics, evals.
- **Model routing** — production apps increasingly use a router/orchestrator:
  cheap fast models (Gemini Flash-class, DeepSeek) for simple tasks, frontier
  models reserved for hard reasoning/agentic work. Reduces both cost and
  vendor lock-in.
- **Adaptive reasoning / effort control** — Anthropic's Adaptive Reasoning
  (4.6 generation, Feb 2026) lets the model decide internally whether and how
  much to think; the Effort parameter (Low/Medium/High/Max) puts that dial in
  the caller's hands. OpenAI exposes reasoning-effort on its thinking
  variants. Paying for deep reasoning only when the task needs it is one of
  the biggest new cost levers.
- **Output-token efficiency as a model feature** — vendors now compete on
  fewer output tokens for the same result (e.g. Gemini 3.6 Flash produces 17%
  fewer output tokens than 3.5 Flash on the same tasks).
- **Managed memory** — Anthropic's agent-memory beta persists knowledge across
  sessions (with a "dreaming" consolidation pass), so agents stop re-deriving
  context every session — an efficiency feature, not just a UX one.

## 2. Agent & context engineering (the newest discipline)

- The field converged on four strategies: **write, select, compress, isolate**
  (Anthropic's context-engineering framing).
- **Compaction** — automatic context compaction in tool-heavy agentic
  workflows shows large real reductions (a documented five-ticket
  customer-service pipeline dropped from 208K to 86K tokens, −58.6%); good
  compression strategies preserve constraints/decisions while replacing old
  history. Claude Code auto-compacts at ~95% of the context window; run it
  proactively instead.
- **Subagent isolation** — a lead agent stays clean holding task+constraints;
  ephemeral subagents burn tens of thousands of exploration tokens in their
  own context and return only 1–2K-token condensed summaries. Detailed search
  context never pollutes the orchestrator.
- **Selective tool loading** — semantic search over tool descriptions to load
  only relevant tools per task (e.g. LangGraph Bigtool; Claude Code's deferred
  ToolSearch) instead of paying for hundreds of tool schemas every turn.
- Counter-trend worth tracking: some teams report *stopping* aggressive
  compaction because lossy summaries cause re-work — compression must earn its
  place per workload.

## 3. Model architecture trends

- **Small language models (SLMs)** — NVIDIA research: 40–70% of enterprise AI
  tasks are handled more efficiently by models under 10B parameters — the
  superior choice on speed/cost/reliability, not a compromise. SLMs reportedly
  cut AI industry carbon emissions ~40% in 2025.
- **Mixture-of-experts** — sparse activation delivers large-model capability
  at small-model inference cost (e.g. Gemma 4 26B-A4B activates only 4B
  params per forward pass). Active research: distilling/pruning MoE back into
  dense models, task-aware expert offloading (eMoE).
- **Distillation** — transferring reasoning patterns from frontier teachers
  into compact students is now standard practice; combined MoE+distillation
  pipelines (e.g. LLaVA-MoD) train small multimodal models from large ones.

## 4. Serving-infrastructure techniques

- **Quantization** — FP8/INT8/INT4 weights cut memory 2–4x; since decode is
  memory-bandwidth-bound, 4-bit weights read up to 4x faster. AWQ/GPTQ keep
  sensitive weights precise for near-FP16 quality at INT4 speed. KV-cache
  quantization (KVTuner-style layer-wise mixed precision) is the newer frontier.
- **Speculative decoding** — a small draft model proposes tokens the large
  model verifies in parallel: 1.5–3x speedups. Newer variants are
  self-speculative with quantized KV caches (QuantSpec) or speculate the
  *prefill* for time-to-first-token (Speculative Prefill).
- **KV-cache & prefix reuse** — prefix caching (SGLang RadixAttention,
  vLLM) eliminates redundant prefill across requests sharing a prefix;
  cache-aware scheduling routes requests to maximize hit rates.
- **Disaggregated prefill/decode** — prefill is compute-bound, decode is
  memory-bound, so splitting them into separately scaled worker pools yields
  ~2x throughput; SGLang has published 2.7x decode-throughput results on
  GB200 NVL72 clusters. 2026 research explores unifying aggregation vs.
  disaggregation dynamically per workload.
- **Stacking matters** — batch inference + KV caching + quantization +
  speculative decoding together reduce energy up to ~73% vs. unoptimized
  baselines; each individual technique is worth ~1.5–4x on its own.

## Practical takeaways for this repo's workflow

- Order prompts static-first so platform caches hit (system prompt, skills,
  docs before volatile context).
- Route by task difficulty; default to the smallest model that passes evals.
- Push anything async to batch endpoints for the flat 50%.
- Set effort/reasoning budget explicitly instead of paying frontier default.
- Use subagents for exploration and keep the orchestrator context clean;
  compact proactively, but verify compaction isn't causing re-work.

## Sources

- [Google Cloud — five techniques to reach the efficient frontier of LLM inference](https://cloud.google.com/blog/topics/developers-practitioners/five-techniques-to-reach-the-efficient-frontier-of-llm-inference)
- [DataNorth — LLM cost optimization: caching, batching, routing](https://datanorth.ai/blog/llm-cost-optimization-prompt-caching-batching-routing)
- [DevToolLab — prompt caching in 2026](https://devtoollab.com/blog/prompt-caching-guide)
- [Anthropic — effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Google Developers Blog — context-aware multi-agent framework for production](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [Louis Bouchard — why we stopped compacting our agent's context](https://www.louisbouchard.ai/context-engineering-2026/)
- [Sombra — token optimization for agentic AI](https://sombrainc.com/blog/token-optimization)
- [HackerNoon — small language models have a trillion-dollar future](https://hackernoon.com/small-language-models-have-a-trillion-dollar-future)
- [ACM Computing Surveys — inference optimization for MoE models](https://dl.acm.org/doi/10.1145/3794845)
- [arXiv — QuantSpec: self-speculative decoding with quantized KV cache](https://arxiv.org/pdf/2502.10424)
- [arXiv — KVTuner: layer-wise mixed-precision KV cache quantization](https://arxiv.org/pdf/2502.04420)
- [arXiv — Speculative Prefill: turbocharging TTFT](https://arxiv.org/pdf/2502.02789)
- [vLLM blog — anatomy of a high-throughput inference system](https://vllm.ai/blog/2025-09-05-anatomy-of-vllm)
- [TECHSY — vLLM vs SGLang 2026 H100 benchmarks](https://techsy.io/en/blog/vllm-vs-sglang)
- [Spheron — prefill/decode disaggregation 2026 guide](https://www.spheron.network/blog/prefill-decode-disaggregation-gpu-cloud/)
- [Linas — everything Anthropic shipped in 2026](https://linas.substack.com/p/anthropic-claude-2026-every-launch-guide)
- [explainx.ai — Claude's effort parameter guide](https://explainx.ai/blog/claude-effort-parameter-model-selection-guide-2026)
- [Syncfusion — best LLM APIs in 2026](https://medium.com/syncfusion/best-llm-apis-in-2026-comparing-openai-claude-gemini-azure-bedrock-mistral-deepseek-a5fcfefa2f85)
- [Redwerk — LLM inference optimization techniques](https://redwerk.com/blog/llm-inference-optimization-techniques/)
