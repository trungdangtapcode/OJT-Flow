# Framework Architecture

The backbone should let the system grow without breaking its shape. The scaffold uses Clean Architecture plus Ports and Adapters:

- Business contracts live in `core`.
- Use cases live in `application`.
- Deterministic tools live in `data_tools`.
- Agents are role wrappers in `agents`.
- Concrete adapters live in `infrastructure`.
- HTTP/API code lives at the outer edge in `interfaces/api`.

## Framework Stack

| Area | Framework / library | Role |
| --- | --- | --- |
| API | FastAPI | Accept requests, validate request schemas, expose `/api/v1/...` routes |
| Contracts | Pydantic v2 | Typed domain contracts, request/response contracts, schema validation |
| Parsing | Python `json`, `csv`, PyYAML | Deterministic JSON/YAML/CSV parsing |
| Tests | pytest | Test backbone workflow, API, and data tools |
| Current storage | In-memory adapters | Run scaffold and tests quickly; replace later with DB adapters |
| Current retrieval | Static knowledge repository | Trusted evidence fixture; replace later with real RAG |
| Current workflow | Custom `WorkflowService` | Orchestrate the first vertical slice; replace or wrap later with LangGraph |
| Current MCP | Boundary placeholder | Direct Python tools first; MCP wrappers after contracts stabilize |

## Layer Diagram

```text
HTTP / FastAPI
  src/ojtflow/interfaces/api
        |
        v
Application use case
  src/ojtflow/application/workflow_service.py
        |
        +--> Agents
        |     src/ojtflow/agents
        |
        +--> Ports
        |     src/ojtflow/application/ports.py
        |
        +--> Deterministic tools
              src/ojtflow/data_tools
        |
        v
Core contracts and policies
  src/ojtflow/core

Infrastructure adapters implement application ports:
  src/ojtflow/infrastructure/storage
  src/ojtflow/infrastructure/retrieval
```

## Dependency Rule

Allowed direction:

```text
interfaces/api -> application -> agents -> data_tools -> core
interfaces/api -> application -> infrastructure
application -> core
agents -> core
data_tools -> core
infrastructure -> core
medical -> core
```

Forbidden:

- `core` must not import FastAPI, databases, cloud SDKs, LLM providers, or MCP runtimes.
- `data_tools` must not call an LLM.
- `agents` must not write files or export data directly; they must go through application and tool boundaries.
- `retrieval` must not mutate workflow state directly.
- `interfaces/api` must not contain business logic.

## Current Code Mapping

| Concern | Current file |
| --- | --- |
| Workflow state contract | `src/ojtflow/core/contracts/workflow.py` |
| Event contract | `src/ojtflow/core/contracts/events.py` |
| Issue/evidence/review contracts | `src/ojtflow/core/contracts/issue.py`, `evidence.py`, `review.py` |
| Risk policy | `src/ojtflow/core/policy/risk_rules.py` |
| Tool permission policy | `src/ojtflow/core/policy/permissions.py` |
| Parse/profile/validate/convert | `src/ojtflow/data_tools/` |
| Agents | `src/ojtflow/agents/` |
| Main orchestration | `src/ojtflow/application/workflow_service.py` |
| Storage ports | `src/ojtflow/application/ports.py` |
| In-memory adapters | `src/ojtflow/infrastructure/storage/in_memory.py` |
| Static knowledge adapter | `src/ojtflow/infrastructure/retrieval/static.py` |
| FastAPI app | `src/ojtflow/interfaces/api/app.py` |

## Why This Architecture

OJTFlow must separate judgment from execution:

- Foundation models and agents may understand intent, explain, and suggest.
- Deterministic tools perform parse, validation, and conversion.
- Policy decides whether human review is required.
- Workflow state stores the current truth.
- The event stream makes every step auditable.

Because of that, the framework should prioritize typed boundaries over a quick demo. FastAPI and Pydantic fit because API contracts and domain contracts can be controlled tightly. LangGraph, MCP, RAG, and model providers can be added later because the application layer already has ports and interfaces.

## Framework Growth Path

| Area | Current | Later |
| --- | --- | --- |
| Workflow runtime | Synchronous `WorkflowService` | LangGraph durable graph, queue worker |
| Storage | In-memory | SQLite/PostgreSQL, object store |
| Retrieval | Static evidence | Hybrid search, vector DB, reranker, GraphRAG |
| Tool access | Direct Python functions | MCP servers wrapping stable tools |
| UI | FastAPI docs/API | Review UI, progress timeline |
| Observability | Event list | OpenTelemetry, Prometheus, audit dashboard |

## Design Pattern Rules

### Entity / Contract

Core objects such as `WorkflowState`, `ValidationReport`, `Evidence`, and `HumanReview` are stable contracts. Adding fields is acceptable; changing the meaning of fields requires versioning.

### Use Case

`WorkflowService` is the application use case. It does not know about HTTP or a concrete database. It only calls ports and agents.

### Port

`DatasetStore`, `WorkflowRepository`, `EventRepository`, and `KnowledgeRepository` are interfaces. Adapters can be in-memory, SQLite, PostgreSQL, S3/GCS, Qdrant, or other infrastructure.

### Adapter

Adapters live outside the domain. They can be replaced without changing the contracts.

### Agent

An agent receives typed input, calls deterministic services or application services, and returns `AgentResult`. Agents must not keep their own state outside workflow state.

### Policy

Policies such as review triggers, PHI heuristics, and prompt-injection heuristics live in `core/policy` so every layer uses the same rules.

