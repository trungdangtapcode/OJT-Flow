# Backbone Blueprint

This folder makes the implementation plan less abstract. It explains which framework owns each layer, how data moves through the system, how workflows pause and resume, which schemas and contracts are the source of truth, and how later modules must plug into the backbone.

Read in this order:

1. `01_framework_architecture.md` - framework stack, clean architecture, dependency rules, and module ownership.
2. `02_dataflow.md` - end-to-end dataflow from request to output and audit.
3. `03_workflow_state_machine.md` - workflow states, events, human review, and failure paths.
4. `04_schema_contracts.md` - workflow, issue, evidence, review, tool, and storage contracts.
5. `05_extension_points.md` - how RAG, MCP, Graph-NER, OCR/DICOM, LangGraph, DB, and MLOps connect to the backbone.

Central rules:

- `core` is the source of truth for contracts and policies.
- `application` coordinates use cases.
- `data_tools` executes deterministic operations.
- `agents` are role wrappers around tools and use cases; they do not mutate data freely.
- `infrastructure` can change, but domain contracts should stay stable.
- `interfaces/api` only translates HTTP requests and responses into application calls.

