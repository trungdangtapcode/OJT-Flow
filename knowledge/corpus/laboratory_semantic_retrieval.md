# Laboratory Semantic Retrieval Corpus

FHIR Observation, LOINC, and UCUM are common grounding targets for laboratory
data workflows. A laboratory result transformation should preserve the source
test name, measured value, unit text, patient identifier, and observation date
before any downstream mapping.

When a row mentions HbA1c or glucose without a unit, retrieval should surface
unit terminology evidence and human review governance. Coding suggestions must
remain evidence-grounded and must not become diagnosis, treatment, triage, or
medication advice.
