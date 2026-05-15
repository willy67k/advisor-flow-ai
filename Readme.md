# Advisor Flow AI

**AI-native workflow platform for financial advisors and wealth management operations.**

_（中文：面向理財顧問與財富管理營運的 AI 原生工作流程平台。）_

Advisor Flow AI is a production-oriented system for document processing, meeting prep, compliance review, operational workflows, and AI-assisted task execution. It connects AI to real operations through orchestration, approval pipelines, auditability, and human-in-the-loop patterns.

_（本專案以「可上線營運」為目標，把 AI 接到實際流程：編排、簽核、稽核與人在回路。）_

---

## Core vision

Modern advisory work involves heavy operational overhead: meeting prep, CRM updates, compliance, onboarding, summarization, follow-ups, and action tracking.

_（現代顧問工作負載很高：會議準備、CRM、法遵、開戶、摘要、後續追蹤與待辦。）_

Advisor Flow AI turns these into **pipelines** with human review, traceability, and structured execution—not a thin chat wrapper.

Intended shape:

```
| Role                   | Meaning                   |
| ----                   | -------                   |
| AI operational system  | AI 驅動的營運系統          |
| Workflow orchestration | 工作流程編排平台           |
| Productivity workspace | AI 原生協作工作台          |
| Enterprise AI          | 具法遵意識的企業級 AI 應用  |
```

---

## Key features

### AI workflow orchestration

_（AI 工作流程編排）_

- Multi-step flows with **LangGraph**, stateful execution, human-in-the-loop approvals, retries/fallbacks, validated structured outputs.

**Example:** upload transcript → summarize → extract actions → CRM draft → compliance validation → human approval → finalize.

### AI copilot workspace

_（顧問用 AI 工作區）_

- Context-aware chat, streaming, tool timeline, citations, memory context, workflow status.

### Document intelligence

_（文件智慧：解析、向量、RAG）_

- PDF ingestion, OCR, semantic chunking, embeddings, RAG, summarization, risk/compliance-oriented analysis.

### Compliance & approvals

_（合規與簽核）_

- Approval flows, audit logs, traceability, permission-based access, AI action review, gating for sensitive steps.

### AI agents

_（代理能力概要）_

- Meeting summaries, follow-up drafts, risk-text analysis, missing compliance signals, structured extraction, suggested next steps.

---

## Tech stack

### Monorepo

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| TurboRepo  | Monorepo orchestration       |
| Yarn       | Workspace package management |

### Frontend

| Technology                | Purpose               |
| ------------------------- | --------------------- |
| React / TypeScript / Vite | App & build           |
| Zustand / TanStack Query  | Client & server state |
| Tailwind CSS / shadcn/ui  | Styling & components  |
| React Hook Form / Zod     | Forms & validation    |
| Framer Motion / PDF.js    | Motion & PDF          |
| EventSource / SSE         | Streaming AI          |

### Backend

| Technology                  | Purpose                 |
| --------------------------- | ----------------------- |
| Django / DRF                | API                     |
| Uvicorn                     | ASGI                    |
| Pydantic                    | Schema validation       |
| SQLAlchemy / Alembic        | ORM & migrations        |
| PostgreSQL / Redis / Celery | Data, cache, async jobs |
| Ruff                        | Lint & format           |

### AI / LLM

| Technology                  | Purpose                     |
| --------------------------- | --------------------------- |
| LangChain / LangGraph       | LLM & stateful workflows    |
| LangSmith                   | Tracing                     |
| OpenAI / Gemini / Anthropic | Model providers             |
| pgvector                    | Vector search               |
| Instructor / tiktoken       | Structured outputs & tokens |
| RAG pipeline                | Retrieval                   |

### DevOps

| Technology              | Purpose                  |
| ----------------------- | ------------------------ |
| Docker / Docker Compose | Containers & local stack |

---

## Core concepts

### 1. Human-in-the-loop

_（敏感操作不自動放行；需核准、可查、可回溯。）_

AI does **not** directly execute sensitive operations. Critical paths require approval, review, audit trails, and rollback where applicable.

### 2. Workflow-first

_（以流程為中心，而非單一提示詞。）_

Workflows encode state transitions, tools, retries, approval states, and audit records.

### 3. Structured outputs

_（輸出要可驗證：Pydantic、JSON、解析與降級策略。）_

Pydantic schemas, structured JSON, deterministic parsing, fallback validation—for reliability in enterprise settings.

### 4. Observability

_（可觀測：token、trace、log、prompt 版本與失敗分析。）_

Token usage, execution traces, workflow logs, prompt versioning, failure analysis—via LangSmith and internal pipelines.

---

## Example workflows

**Meeting summary** — Upload transcript → chunk/embed → structured summary → client concerns → follow-ups → CRM draft → approval → audit log.

**Compliance review** — Analyze advisor content → prohibited phrases → disclosures → risk score → review task if needed.

**Email draft** — Client context → recent meetings → draft → compliance check → approval → send via integration.

---

## Architecture goals

_（架構目標：可稽核、可靠編排、模組化管線、異步擴展、清楚的 AI UX、可多供應商切換。）_

AI-native ops, enterprise auditability, reliable orchestration, modular AI/async scale, clear UX, provider-agnostic integration.

---

## Roadmap (ideas)

Multi-agent collaboration, tool sandboxes, MCP, voice ingestion, real-time collaboration, autonomous policy layers, eval pipelines, durable agent memory.

_（規劃方向：多代理、工具沙箱、MCP、語音會議、即時協作、自治策略、評測、記憶持久化等。）_

---

## Local development

### Frontend

```bash
yarn install
yarn dev
```

### Backend

```bash
uv sync
uvicorn app.main:app --reload
```

### Workers

```bash
celery -A app.worker worker --loglevel=info
```

_（中文：前端用 Yarn；後端用 `uv` 安裝依賴並啟動 ASGI；非同步任務另起 Celery worker。）_

---

## License

MIT
