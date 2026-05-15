# Advisor Flow AI

**AI-native workflow platform for financial advisors and wealth management operations.**

_Advisor Flow AI／理財顧問與財富管理營運取向的 AI 工作流程平台。_

Advisor Flow AI is a production-oriented system for document processing, meeting prep, compliance review, operational workflows, and AI-assisted task execution. It connects AI to real operations through orchestration, approval pipelines, auditability, and human-in-the-loop patterns.

_Production-first: the goal is deployable workflows—orchestration, approvals, audit trails, human-in-the-loop (HITL)._

_（可上線導向：編排、簽核、稽核、人在回路。）_

---

## Core vision

Modern advisory work involves heavy operational overhead: meeting prep, CRM updates, compliance, onboarding, summarization, follow-ups, and action tracking.

Advisor Flow AI turns these into **pipelines** with human review, traceability, and structured execution—not a thin chat wrapper.

_顧問日常工作負載高；本專案以「可驗證、可追蹤的流程」而非聊天外殼為核心。_

Intended shape:

| Role                   | Meaning                                                     |
| ---------------------- | ----------------------------------------------------------- |
| AI operational system  | Operational system driven by AI pipelines _（AI 驅動營運）_ |
| Workflow orchestration | Stateful steps, tools, approvals, audit _（流程編排）_      |
| Productivity workspace | Advisor-facing AI workspace UX _（顧問工作區）_             |
| Enterprise AI          | Compliance-aware, reviewable automation _（法遵／簽核）_    |

---

## Key features

### AI workflow orchestration

Multi-step flows with **LangGraph**, stateful execution, human-in-the-loop approvals, retries/fallbacks, validated structured outputs.

**Example:** upload transcript → summarize → extract actions → CRM draft → compliance validation → human approval → finalize.

_（AI 多步編排與結構化輸出。）_

### AI copilot workspace

Context-aware chat, streaming, tool timeline, citations, memory context, workflow status.

_（顧問用的 AI 工作區／串流與工具軌跡。）_

### Document intelligence

PDF ingestion, OCR, semantic chunking, embeddings, RAG, summarization, risk/compliance-oriented analysis.

_（文件解析、向量、RAG。）_

### Compliance & approvals

Approval flows, audit logs, traceability, permission-based access, AI action review, gating for sensitive steps.

_（合規、簽核、稽核軌跡。）_

### AI agents

Meeting summaries, follow-up drafts, risk-text analysis, missing compliance signals, structured extraction, suggested next steps.

_（代理型任務例：摘要、草稿、風險字句、抽取。）_

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

AI does **not** directly execute sensitive operations. Critical paths require approval, review, audit trails, and rollback where applicable.

_（敏感步驟不自動放行；需核准與稽核。）_

### 2. Workflow-first

Workflows encode state transitions, tools, retries, approval states, and audit records.

_（以流程與狀態為中心，而非單一 prompt。）_

### 3. Structured outputs

Pydantic schemas, structured JSON, deterministic parsing, fallback validation—for reliability in enterprise settings.

_（輸出可驗證：schema、解析、降級。）_

### 4. Observability

Token usage, execution traces, workflow logs, prompt versioning, failure analysis—via LangSmith and internal pipelines.

_（Token、trace、log、版本與失敗分析。）_

---

## Example workflows

**Meeting summary** — Upload transcript → chunk/embed → structured summary → client concerns → follow-ups → CRM draft → approval → audit log.

**Compliance review** — Analyze advisor content → prohibited phrases → disclosures → risk score → review task if needed.

**Email draft** — Client context → recent meetings → draft → compliance check → approval → send via integration.

---

## Architecture goals

AI-native ops, enterprise auditability, reliable orchestration, modular AI/async scale, clear UX, provider-agnostic integration.

_（可稽核、可靠編排、模組化管線、異步擴展、清楚 AI UX、多供應商。）_

---

## Roadmap (ideas)

Multi-agent collaboration, tool sandboxes, MCP, voice ingestion, real-time collaboration, autonomous policy layers, eval pipelines, durable agent memory.

_（多代理、沙箱、MCP、語音、即時協作、策略層、評測、記憶等方向。）_

---

## Local development

### Docker Compose (recommended)

Brings up **Postgres (pgvector)**, **Redis**, **Django/Uvicorn**, **Celery worker**, and **Vite** from the repo root (`docker-compose.yml`). The backend runs migrations on start. Use a real worker queue in Compose: keep **`CELERY_TASK_ALWAYS_EAGER=false`** so tasks are not executed only inside the API process.

```bash
# Compose reads `.env` at the repo root (copy from the example for ports, DB creds, optional keys).
cp compose.example.env .env

# Django/Pydantic also load `packages/backend/.env` — set OPENAI_* and other keys you need.
cp packages/backend/.env.example packages/backend/.env

docker compose up --build
```

- **Frontend:** <http://localhost:3800> — Vite proxies **`/api`** to the **`backend`** service on the Compose network (`VITE_DEV_PROXY_TARGET`, default `http://backend:3801`).
- **API:** <http://localhost:3801> — OpenAPI UI: <http://localhost:3801/api/docs/>.
- **Flower (optional):** `docker compose --profile flower up --build` — default UI <http://localhost:5555>.

Do not commit secrets. Use the repo root **`.env`** for Compose variable substitution and **`packages/backend/.env`** for the Django app.

_（敏感值勿入庫；Compose 用根目錄 `.env`，應用程式用 `packages/backend/.env`。）_

### Native (Yarn + uv on the host)

#### Frontend (repo root)

```bash
yarn install
yarn dev
```

#### Backend (`packages/backend`)

```bash
cd packages/backend
uv sync
yarn dev
# Same as: uv run uvicorn app.main:app --reload --port 3801
```

Without **`DATABASE_URL`**, Django can fall back to local SQLite for lightweight dev; Postgres + pgvector (and pytest defaults) align with **`packages/backend/.env.example`**.

#### Celery worker (same directory)

```bash
cd packages/backend
yarn worker
# Same as: uv run celery -A app.worker:celery_app worker -l INFO --pool=solo
```

Set **`CELERY_TASK_ALWAYS_EAGER=false`** when using Redis-backed queues. With **`CELERY_TASK_ALWAYS_EAGER=true`** (see `.env.example`), you can skip a separate worker; tasks run in-process.

_（本機開發：eager 模式可省 worker；要真佇列需 Redis + worker。）_

---

## License

MIT
