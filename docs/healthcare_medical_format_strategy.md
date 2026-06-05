


# Healthcare And Medical Data Format Strategy

## Decision

OJTFlow should not define healthcare data as one simple CSV or JSON shape. The correct strategy is a layered healthcare data model:

1. accept messy operational inputs;
2. parse and validate them into internal workflow contracts;
3. normalize clinical meaning into FHIR-like JSON resources;
4. attach evidence, provenance, audit, and human-review state;
5. later export or map to real interoperability and analytics standards.

The current implementation is a v0 backend spine, not a complete medical interoperability platform. It currently supports CSV/JSON/YAML/NDJSON ingestion, a synthetic lab schema, FHIR-like resource profiling, OCR evidence stubs, validation reports, review gates, audit events, and Postgres-backed workflow persistence. The full project scope in the proposal is broader: FHIR, Bulk FHIR, HL7 v2, DICOM, OCR/document AI, Graph-NER, RAG, OMOP, terminology normalization, and healthcare governance.

## Research Basis

| Standard | What It Is | Role In OJTFlow |
| --- | --- | --- |
| [HL7 FHIR](https://hl7.org/fhir/resource.html) | Resource-based healthcare exchange standard. Resources identify their type with `resourceType` and contain structured data elements. | Primary canonical clinical model. Use FHIR-like JSON first, full profile validation later. |
| [FHIR JSON/XML/RDF formats](https://fhir.hl7.org/fhir/formats.html) | FHIR resources can be represented in JSON, XML, and Turtle/RDF. | Use JSON because the API, Pydantic contracts, workflow state, and frontend already speak JSON. |
| [FHIR Bundle](https://hl7.org/fhir/bundle.html) | Container for groups of FHIR resources used for transfer, storage, messages, search results, documents, and collections. | Canonical package for multi-resource workflow output. |
| [FHIR Observation](https://www.hl7.org/fhir/observation.html) | Resource for measurements and assertions such as lab values, vital signs, and clinical observations. | Primary v0 lab-result target. |
| [FHIR Patient](https://hl7.org/fhir/patient.html) | Demographic and administrative information for a person receiving care. | Required for real clinical context; synthetic `patient_id` maps to a Patient reference in v0. |
| [FHIR DiagnosticReport](https://hl7.org/fhir/R4/diagnosticreport.html) | Findings and interpretation of diagnostic tests, often grouping observations, text, images, and reports. | Future target for lab panels, radiology reports, and OCR-derived reports. |
| [FHIR DocumentReference](https://fhir.hl7.org/fhir/documentreference.html) | Metadata and reference to clinical documents, binary content, external documents, DICOM exchange, or HL7 v2 query output. | Use for scanned forms, referral letters, clinical notes, and source-document linkage. |
| [FHIR ImagingStudy](https://hl7.org/fhir/imagingstudy.html) | Details of DICOM studies and imaging-related metadata. | Use for DICOM metadata references; do not process raw DICOM pixels in v0. |
| [FHIR Provenance](https://fhir.hl7.org/fhir/provenance.html) | Records how a resource came to exist or changed, including source and transformation context. | Future standards-aligned version of OJTFlow evidence and transformation lineage. |
| [FHIR AuditEvent](https://www.hl7.org/fhir/R5/auditevent.html) | Record of security, privacy, and operational events: who, what, where, when, and why. | Future standards-aligned version of workflow audit events. |
| [FHIR NDJSON](https://fhir.hl7.org/fhir/nd-json.html) | Newline-delimited JSON representation used for FHIR bulk data transfer. | Population-scale ingestion/export target after single-workflow v0 is stable. |
| [HL7 v2](https://hl7.eu/HL7v2x/v251/std251/ch02.html) | Event-message standard based on delimited segments such as MSH, PID, OBR, and OBX. | Future adapter for hospital event feeds; not the internal canonical model. |
| [DICOM](https://www.dicomstandard.org/about) | Standard for medical images and related information. | Future imaging data plane. v0 stores references and metadata only. |
| [LOINC](https://loinc.org/) | Code system for lab tests, observations, measurements, and documents. | Future normalization target for `lab_name` and observation codes. |
| [UCUM](https://ucum.nlm.nih.gov/ucum-service.html) | Unified Code for Units of Measure. | Future validation target for lab units such as `%`, `mg/dL`, `mmol/L`. |
| [SNOMED CT](https://www.nlm.nih.gov/healthit/snomedct/faq.html) | Broad clinical terminology for problems, findings, procedures, and other clinical concepts. | Future terminology target for conditions, procedures, findings, and Graph-NER linking. |
| [OMOP CDM](https://ohdsi.github.io/CommonDataModel/) | Common data model for observational healthcare analytics and research. | Future analytics warehouse target, separate from FHIR exchange. |
| [Google Cloud Healthcare API](https://docs.cloud.google.com/healthcare-api/docs/introduction) | Managed stores for FHIR, HL7 v2, and DICOM healthcare data. | Possible industrial deployment path, not required for local v0. |
| [HHS HIPAA de-identification guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html) | Guidance for handling and de-identifying protected health information. | Supports PHI detection, masking, review gates, and no raw PHI in logs. |

## Codebase Reality

Current source code supports:

- `DataFormat`: `json`, `yaml`, `csv`, `ndjson`, `unknown`;
- `WorkflowState`: input references, intent, steps, profile, validation, review, output, explanation, handoff context, risk flags, audit refs;
- `Evidence`: source type, source id, claim, locator, confidence, trust level;
- `ValidationReport`: schema confidence, severity summary, issues, review requirement;
- `OcrField`: page, field name, value, bounding box, confidence, source reference, review flag;
- `FhirProfile`: lightweight detection of `resourceType`, `Bundle.entry`, resource counts, issues, and Graph-NER/RAG handoff context;
- `DicomReference`: study/series/instance/frame references, de-identification flag;
- `VisualEvidenceArtifact`: masks, boxes, frames, labels, artifact refs, confidence, clinician-review flag.

This means the project already has the right backbone shape. The weak point is not the spine. The weak point is that the healthcare format doc must describe the full layered model instead of only `lab_result_v1`.

## Format Layers

| Layer | Format | Purpose |
| --- | --- | --- |
| Raw input | CSV, JSON, YAML, NDJSON, uploaded text/files | Accept real-world operational data as-is. |
| Parse result | `ParsedData` and `DataProfile` | Preserve rows, fields, source refs, parser warnings, inferred types, missingness, and PHI flags. |
| Validation | `ValidationReport` and `Issue` | Store data-quality findings, schema mismatch, malformed rows, missing units, PHI risk, prompt injection, and review requirement. |
| Clinical canonical model | FHIR-like JSON | Represent clinical meaning as resources such as Patient, Encounter, Observation, DiagnosticReport, Condition, Procedure, MedicationRequest, DocumentReference, ImagingStudy. |
| Evidence model | `Evidence`, OCR boxes, DICOM references, visual artifacts | Link every claim or transformation to source rows, pages, boxes, studies, masks, events, or human decisions. |
| Workflow model | `WorkflowState`, `WorkflowStep`, audit events, review state | Preserve progress, approval, failures, output refs, and restart-safe traceability. |
| Terminology model | LOINC, UCUM, SNOMED CT, later local code aliases | Normalize clinical names, units, findings, procedures, and concepts. |
| Analytics target | OMOP CDM, Parquet/lakehouse, BigQuery later | Support research, cohorts, population analysis, and model evaluation. |
| Exchange targets | FHIR Bundle, Bulk FHIR NDJSON, HL7 v2, CDA/DocumentReference, DICOM | Support integration with hospitals and external systems. |

## Canonical Resource Set

OJTFlow should treat these as the target clinical resource families:

| Resource | Use |
| --- | --- |
| `Patient` | Subject identity, synthetic patient references, demographics later. |
| `Encounter` | Visit or care context. Needed before serious clinical timeline work. |
| `Observation` | Lab results, vitals, measurements, extracted clinical facts. |
| `DiagnosticReport` | Grouped lab panels, radiology reports, OCR-derived diagnostic documents. |
| `Condition` | Problems, diagnoses, findings requiring clinical interpretation. |
| `Procedure` | Performed procedures or interventions. |
| `MedicationRequest` / `MedicationStatement` | Medication orders and reported medication use. |
| `DocumentReference` | Clinical notes, scanned forms, referrals, reports, external document pointers. |
| `ImagingStudy` | DICOM study metadata and imaging workflow references. |
| `Provenance` | Source and transformation lineage for generated resources. |
| `AuditEvent` | Security/privacy/operational audit trail. |

V0 should not implement every resource. V0 should define profiles and mapping contracts so the architecture does not paint itself into a lab-only corner.

## Internal Canonical Package

The internal output should be a project envelope around FHIR-like resources, not raw FHIR alone:

```json
{
  "package_type": "ojtflow_clinical_package",
  "schema_version": "clinical_package.v0",
  "workflow_id": "wf_xxx",
  "raw_input": {
    "dataset_ref": "storage://datasets/input-001",
    "input_hash": "sha256:...",
    "declared_format": "csv",
    "detected_format": "csv"
  },
  "clinical_bundle": {
    "resourceType": "Bundle",
    "type": "collection",
    "entry": []
  },
  "validation_report": {},
  "evidence": [],
  "provenance": [],
  "review": {},
  "audit_event_refs": [],
  "handoff_context": {
    "graphner_ready": true,
    "rag_query_terms": [],
    "terminology_candidates": []
  }
}
```

This is the right shape because OJTFlow is not only an exchange converter. It is a governed workflow system. The workflow, validation, evidence, and review state are first-class outputs.

## V0 Lab Mapping

Current `lab_result_v1` should map into FHIR-like `Observation` resources.

| `lab_result_v1` field | FHIR-like target | Notes |
| --- | --- | --- |
| `patient_id` | `Observation.subject.reference` plus optional `Patient.identifier` | Treat as sensitive. Use synthetic IDs in demos. |
| `date` | `Observation.effectiveDateTime` | Validate ISO `YYYY-MM-DD`; normalize only after review. |
| `lab_name` | `Observation.code.text`; later `Observation.code.coding` with LOINC | Keep text in v0, add LOINC candidates later. |
| `value` | `Observation.valueQuantity.value` | Must be numeric when represented as a Quantity. |
| `unit` | `Observation.valueQuantity.unit`; later `Observation.valueQuantity.system/code` with UCUM | Missing unit requires review. |
| source row | `Evidence.locator.row` and future `Provenance` | Do not lose row-level traceability. |

Example target:

```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "fullUrl": "urn:uuid:observation-1",
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "code": {
          "text": "HbA1c"
        },
        "subject": {
          "reference": "Patient/P001"
        },
        "effectiveDateTime": "2026-01-01",
        "valueQuantity": {
          "value": 7.4,
          "unit": "%"
        }
      }
    }
  ]
}
```

## Roadmap By Format Maturity

### V0: Implemented Backbone

- Ingest CSV/JSON/YAML/NDJSON.
- Validate against `lab_result_v1`.
- Detect FHIR-like `resourceType` and `Bundle.entry`.
- Store workflow state, steps, events, evidence, review, and output refs.
- Accept OCR evidence as structured page/field/bounding-box/confidence records.
- Keep DICOM as metadata references only.
- Make no diagnosis or treatment recommendation.

### V1: Healthcare Canonical Layer

- Add explicit internal `ClinicalPackage` contract.
- Add FHIR-like resource builders for `Patient`, `Observation`, `DiagnosticReport`, and `DocumentReference`.
- Add mapping profiles from `lab_result_v1` to FHIR-like `Observation`.
- Add terminology candidate fields for LOINC and UCUM, without requiring perfect coding.
- Add stricter source evidence for every generated resource field.
- Add clinician/human review gates for semantic normalization.

### V2: Interoperability And Analytics

- Add real FHIR profile validation using an HL7 FHIR library or validator service.
- Add Bulk FHIR NDJSON import/export.
- Add HL7 v2 adapter for MSH/PID/OBR/OBX style lab messages.
- Add DICOM metadata ingestion and `ImagingStudy` mapping.
- Add document ingestion through `DocumentReference` and OCR/layout evidence.
- Add OMOP CDM mapping for analytics and research workflows.
- Add terminology service integration for LOINC, UCUM, SNOMED CT, and local aliases.

## Safety Rules

- Do not call v0 output "FHIR compliant"; call it "FHIR-like".
- Do not infer clinical diagnosis or treatment from conversion output.
- Do not silently normalize dates, units, missing values, patient identifiers, or clinical terms.
- Do not export sensitive data without explicit approval.
- Keep source references for every transformed field.
- Treat OCR and model-extracted values as evidence requiring confidence and review.
- Keep audit events append-only.

## Recommended Project Wording

Use this wording in the product and proposal:

> OJTFlow is a governed healthcare data workflow system that accepts messy structured and document-derived inputs, validates them, normalizes selected clinical facts into FHIR-like JSON resources, attaches evidence and provenance, and uses human review gates before medically consequential or sensitive transformations.

This matches the current codebase and leaves room for the full research roadmap.
