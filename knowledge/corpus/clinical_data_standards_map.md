# Clinical Data Standards Map

This document maps OJTFlow retrieval tasks to the healthcare standards and
public datasets that should ground the result. It is intentionally conservative:
retrieval evidence can guide parsing, validation, and explanation, but final
clinical code assignment must remain auditable and reviewable.

## Laboratory Results

Primary standards:

- FHIR Observation for lab-result resource structure.
- LOINC for laboratory test identity, usually in `Observation.code`.
- UCUM for computable units, usually in `Observation.valueQuantity.code`.

Common seed concepts:

- HbA1c: LOINC `4548-4`.
- Glucose in serum or plasma: LOINC `2345-7`.
- Creatinine in serum or plasma: LOINC `2160-0`.
- Sodium in serum or plasma: LOINC `2951-2`.
- Potassium in serum or plasma: LOINC `2823-3`.
- Total cholesterol in serum or plasma: LOINC `2093-3`.

Retrieval behavior:

- Prefer exact field and code evidence when query context includes lab names,
  units, FHIR Observation, or CSV lab result fields.
- Surface missing unit and ambiguous unit evidence before any downstream
  transformation.
- Preserve original `lab_name`, `value`, and `unit` text even when a candidate
  LOINC or UCUM mapping is found.

## Medication Data

Primary standards:

- RxNorm for normalized medication identity.
- FHIR MedicationRequest or MedicationStatement for medication workflow records.
- openFDA for public regulatory label and adverse-event evidence.

Common seed concepts:

- Metformin: RxNorm RxCUI `6809`.
- Metformin: MeSH descriptor `D008687` for literature search context.

Retrieval behavior:

- Treat RxNorm candidate matches as normalization evidence, not automatic final
  mapping.
- For drug safety or adverse-event questions, route toward openFDA and PubMed
  evidence rather than local schema evidence alone.
- Keep dose, route, frequency, and status as separate evidence dimensions.

## Vital Signs

Primary standards:

- FHIR Observation for vital-sign resource structure.
- LOINC for vital-sign observation identity.
- UCUM for computable vital-sign units.

Common seed concepts:

- Systolic blood pressure: LOINC `8480-6`.
- Diastolic blood pressure: LOINC `8462-4`.
- Heart rate: LOINC `8867-4`.
- Oxygen saturation by pulse oximetry: LOINC `59408-5`.
- Body temperature: LOINC `8310-5`.

Retrieval behavior:

- Expand common clinical shorthand such as `BP`, `SBP`, `DBP`, and `HTN` into
  explicit blood-pressure evidence queries before ranking.
- Expand generic `vitals` separately from blood-pressure shorthand so heart
  rate, oxygen saturation, and body-temperature queries are not forced into a
  systolic/diastolic interpretation.
- Prefer separate systolic and diastolic evidence over a combined free-text
  blood-pressure label when validating or explaining structured records.
- Preserve raw readings and units while surfacing candidate LOINC/UCUM
  grounding for review.

## Conditions And Problem Lists

Primary standards:

- FHIR Condition for problem-list and diagnosis resource structure.
- SNOMED CT for clinical finding terminology.
- ICD-10-CM for U.S. diagnosis coding and classification.

Common seed concepts:

- Type 2 diabetes mellitus diagnosis: ICD-10-CM seed code `E11.9`.
- Essential hypertension diagnosis: ICD-10-CM seed code `I10`.

Retrieval behavior:

- Route diagnosis, condition, and problem-list queries to FHIR Condition
  evidence instead of generic Observation evidence.
- Treat SNOMED CT and ICD-10-CM matches as terminology grounding for review,
  not automatic diagnosis-code assignment.
- Preserve original diagnosis text, code-system candidates, clinical status,
  verification status, and source evidence before mapping to downstream FHIR or
  analytics structures.

## Allergies, Intolerances, And Adverse Reactions

Primary standards:

- FHIR AllergyIntolerance for allergy, intolerance, adverse-reaction, and
  reaction-manifestation resource structure.
- SNOMED CT for allergy, sensitivity, intolerance, and manifestation clinical
  concepts.
- RxNorm for medication ingredient or product identity when the reaction
  substance is a drug.

Common seed concepts:

- Penicillin allergy: RxNorm ingredient-level seed code `70618`.
- Latex allergy: SNOMED CT seed code `300916003`.

Retrieval behavior:

- Route allergy, intolerance, adverse-reaction, reaction-substance, and
  manifestation queries to FHIR AllergyIntolerance evidence instead of generic
  medication or Observation evidence.
- Treat RxNorm and SNOMED CT matches as grounding candidates for review, not
  automatic allergy-status, severity, or clinical-safety decisions.
- Preserve original substance text, clinical status, verification status,
  reaction manifestation, recorder/source, uncertainty, and review notes before
  using allergy evidence in downstream safety or transformation workflows.

## Literature And Evidence Search

Primary standards and datasets:

- MeSH for biomedical subject headings.
- PubMed/MEDLINE for biomedical citation retrieval.
- ClinicalTrials.gov for clinical study records.

Common seed concepts:

- Diabetes Mellitus: MeSH descriptor `D003920`.
- Hypertension: MeSH descriptor `D006973`.
- Kidney Failure, Chronic: MeSH descriptor `D007676`.

Retrieval behavior:

- Combine controlled-vocabulary candidates with title/abstract text words.
- Warn operators that PubMed field tags, quoted phrases, and wildcards can alter
  Automatic Term Mapping.
- Use literature retrieval as evidence context, not clinical decision support.

## Analytics Export

Primary standards:

- OMOP CDM for observational analytics export.
- FHIR/LOINC/RxNorm/UCUM as source evidence before mapping.

Retrieval behavior:

- Do not map directly to OMOP until source evidence, validation issues, and
  code confidence are preserved.
- Keep transformation metadata and lossy warnings in the workflow state.

## Review Gates

Human review is required when:

- A value changes meaning.
- A unit is missing or ambiguous.
- A controlled-vocabulary candidate has insufficient confidence.
- Patient identifiers or PHI-like fields are involved.
- Retrieval evidence is from public literature or regulatory data but is being
  used to justify workflow transformation.
