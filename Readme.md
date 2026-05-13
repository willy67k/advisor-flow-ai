# Advisor Flow AI

AI-native workflow platform for financial advisors and wealth management operations.

Advisor Flow AI is a production-oriented AI workflow system designed to assist financial advisors with document processing, meeting preparation, compliance review, operational workflows, and AI-assisted task execution.

The platform focuses on bridging AI systems with real operational workflows through structured orchestration, approval pipelines, auditability, and human-in-the-loop interaction patterns.

---

# Core Vision

Modern financial advisory workflows involve a large amount of operational overhead:

- Meeting preparation
- CRM updates
- Compliance checks
- Client onboarding
- Document summarization
- Follow-up generation
- Action item tracking

Advisor Flow AI transforms these workflows into AI-assisted operational pipelines with human review, traceability, and structured execution.

The system is intentionally designed as:

- AI operational system
- workflow orchestration platform
- AI-native productivity workspace
- compliance-aware enterprise AI application

rather than a simple chatbot wrapper.

---

# Key Features

## AI Workflow Orchestration

- Multi-step AI workflows using LangGraph
- Stateful workflow execution
- Human-in-the-loop approval flow
- Retry / fallback execution handling
- Structured AI outputs with validation

Example workflow:

1. Upload client meeting transcript
2. AI summarizes meeting
3. Extract action items
4. Generate CRM update draft
5. Compliance review agent validation
6. Human approval
7. Final workflow execution

---

## AI Copilot Workspace

Interactive AI workspace for advisors:

- Context-aware AI chat
- Streaming responses
- Tool execution timeline
- Source citations
- AI memory context
- Workflow status visualization

---

## Document Intelligence

- PDF ingestion
- OCR extraction
- Semantic chunking
- Vector embeddings
- Retrieval-Augmented Generation (RAG)
- AI document summarization
- Risk / compliance analysis

---

## Compliance & Approval System

Enterprise-grade operational controls:

- Approval workflows
- Audit logs
- Workflow traceability
- Permission-based access control
- AI action review
- Sensitive operation gating

---

## AI Agent System

AI agents can:

- Generate meeting summaries
- Draft client follow-up emails
- Analyze financial risk statements
- Detect missing compliance fields
- Extract structured client data
- Suggest operational next steps

---

# Tech Stack

---

# Monorepo

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| TurboRepo  | Monorepo orchestration       |
| Yarn       | Workspace package management |

---

# Frontend

| Technology        | Purpose                        |
| ----------------- | ------------------------------ |
| React             | Frontend framework             |
| TypeScript        | Type-safe frontend development |
| Vite              | Frontend build tooling         |
| Zustand           | Lightweight state management   |
| TanStack Query    | Server state management        |
| Tailwind CSS      | Styling system                 |
| shadcn/ui         | UI component system            |
| React Hook Form   | Form management                |
| Zod               | Frontend schema validation     |
| Framer Motion     | Animation system               |
| PDF.js            | PDF rendering                  |
| EventSource / SSE | Streaming AI responses         |

---

# Backend

| Technology            | Purpose                       |
| --------------------- | ----------------------------- |
| Django                | Backend framework             |
| Django REST Framework | REST API layer                |
| Uvicorn               | ASGI server                   |
| Pydantic              | Structured schema validation  |
| SQLAlchemy            | ORM layer for service modules |
| Alembic               | Database migration management |
| PostgreSQL            | Primary relational database   |
| Redis                 | Queue + caching               |
| Celery                | Async task processing         |
| Ruff                  | Linter & Formatter            |

---

# AI / LLM Stack

| Technology    | Purpose                         |
| ------------- | ------------------------------- |
| LangChain     | LLM abstraction layer           |
| LangGraph     | Stateful workflow orchestration |
| LangSmith     | AI tracing & observability      |
| OpenAI API    | LLM provider                    |
| Gemini API    | LLM provider                    |
| Anthropic API | LLM provider                    |
| pgvector      | Vector similarity search        |
| Instructor    | Structured output enforcement   |
| tiktoken      | Token estimation                |
| RAG Pipeline  | Retrieval workflows             |

---

# DevOps / Infra

| Technology     | Purpose             |
| -------------- | ------------------- |
| Docker         | Containerization    |
| Docker Compose | Local orchestration |

---

# Core System Concepts

---

# 1. Human-in-the-loop AI

AI does NOT directly execute sensitive operations.

Critical workflows require:

- approval
- review
- audit traceability
- rollback capability

This mirrors real enterprise AI operational constraints.

---

# 2. Workflow-first Architecture

The platform is designed around workflows instead of isolated prompts.

Each workflow contains:

- state transitions
- tool execution
- retry handling
- approval states
- audit records

---

# 3. Structured AI Outputs

AI outputs are validated using:

- Pydantic schemas
- structured JSON outputs
- deterministic parsing
- fallback validation

This improves reliability for enterprise environments.

---

# 4. AI Observability

All AI executions include:

- token usage tracking
- execution traces
- workflow logs
- prompt versioning
- failure analysis

using LangSmith + internal observability pipelines.

---

# Example Workflows

---

# Meeting Summary Workflow

1. Upload meeting transcript
2. Chunk & embed transcript
3. Generate structured summary
4. Extract client concerns
5. Generate follow-up tasks
6. Draft CRM update
7. Human approval
8. Persist audit log

---

# Compliance Review Workflow

1. Analyze generated advisor response
2. Detect prohibited statements
3. Validate required disclosures
4. Assign risk score
5. Trigger review task if necessary

---

# AI Email Draft Workflow

1. Load client context
2. Retrieve recent meetings
3. Generate personalized draft
4. Compliance validation
5. Human approval
6. Send via integration service

---

# Architecture Goals

- AI-native operational workflow system
- Enterprise-grade auditability
- Reliable orchestration
- Modular AI pipelines
- Async workflow scalability
- Clear AI UX patterns
- Provider-agnostic AI integration

---

# Future Enhancements

- Multi-agent collaboration
- Tool permission sandboxing
- MCP integration
- Voice meeting ingestion
- Real-time collaborative workflows
- Autonomous workflow execution policies
- AI evaluation pipelines
- Agent memory persistence

---

# Local Development

## Frontend

```bash
yarn install
yarn dev
```

## Backend

```bash
uv sync
uvicorn app.main:app --reload
```

## Workers

```bash
celery -A app.worker worker --loglevel=info
```

---

# License

MIT
