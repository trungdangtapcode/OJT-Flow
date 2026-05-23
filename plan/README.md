# OJTFlow Planning Index

Read these in order:

1. `00_master_plan.md` - master implementation plan and delivery phases.
2. `01_scaffolding_backbone.md` - first scaffold to build; defines the system backbone.
3. `backbone_blueprint/` - detailed framework, dataflow, workflow, schema, and extension blueprint.
4. `02_core_workflow_detailed_plan.md` - parse, profile, validate, review, convert, explain.
5. `03_agents_mcp_detailed_plan.md` - agent roles, tool registry, MCP, human review flow.
6. `04_rag_graphner_detailed_plan.md` - RAG, Graph-NER, graph retrieval, SSL gates.
7. `05_medical_multimodal_detailed_plan.md` - OCR, DICOM, visual evidence, Japan-market fit.
8. `06_security_governance_detailed_plan.md` - threat model, PHI/APPI controls, audit, review gates.
9. `07_platform_mlops_detailed_plan.md` - local stack, GCP blueprint, CI/CD, observability, MLOps.
10. `08_evaluation_roadmap_detailed_plan.md` - metrics, golden workflows, release gates, demo path.
11. `09_backend_v0_implementation_status.md` - current backend v0 implementation status after scaffold hardening.

The key recommendation is to build `01_scaffolding_backbone.md` first. It is the backbone that keeps later AI, retrieval, medical, and platform modules from drifting into separate systems.
