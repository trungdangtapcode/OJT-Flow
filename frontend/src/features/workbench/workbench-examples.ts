const sampleCsv =
  "date,patient_id,lab_name,value,unit\n" +
  "2026-01-01,P001,HbA1c,7.4,%\n" +
  "2026/01/02,P002,HbA1c,,\n" +
  "2026-01-03,P003,LDL,131,\n";

const sampleJson = JSON.stringify(
  [
    { date: "2026-01-01", patient_id: "P001", lab_name: "HbA1c", value: 7.4, unit: "%" },
    { date: "2026/01/02", patient_id: "P002", lab_name: "HbA1c", value: "", unit: "" },
    { date: "2026-01-03", patient_id: "P003", lab_name: "LDL", value: 131, unit: "" },
  ],
  null,
  2,
);

const sampleYaml =
  "- date: 2026-01-01\n" +
  "  patient_id: P001\n" +
  "  lab_name: HbA1c\n" +
  "  value: 7.4\n" +
  '  unit: "%"\n' +
  "- date: 2026/01/02\n" +
  "  patient_id: P002\n" +
  "  lab_name: HbA1c\n" +
  "  value: null\n" +
  "  unit: null\n" +
  "- date: 2026-01-03\n" +
  "  patient_id: P003\n" +
  "  lab_name: LDL\n" +
  "  value: 131\n" +
  "  unit: null\n";

const sampleFhirObservation = JSON.stringify(
  {
    resourceType: "Observation",
    status: "final",
    code: { text: "HbA1c" },
    subject: { reference: "Patient/P001" },
    effectiveDateTime: "2026-01-01",
    valueQuantity: {
      value: 7.4,
      unit: "%",
      system: "http://unitsofmeasure.org",
    },
  },
  null,
  2,
);

export type InputExample = {
  data: string;
  fields: string[];
  id: string;
  inputFormat: "csv" | "json" | "yaml";
  instruction: string;
  label: string;
  schemaId: string;
  standard?: string;
  targetFormat: "json" | "yaml" | "csv";
};

export const inputExamples: InputExample[] = [
  {
    id: "csv_lab_result",
    label: "CSV lab rows",
    inputFormat: "csv",
    targetFormat: "json",
    schemaId: "lab_result_v1",
    instruction: "Clean this CSV, convert it to JSON, and explain anomalies.",
    data: sampleCsv,
    fields: ["date", "patient_id", "lab_name", "value", "unit"],
  },
  {
    id: "json_lab_result",
    label: "JSON records",
    inputFormat: "json",
    targetFormat: "yaml",
    schemaId: "lab_result_v1",
    instruction: "Validate these JSON lab records, convert them to YAML, and explain anomalies.",
    data: sampleJson,
    fields: ["date", "patient_id", "lab_name", "value", "unit"],
  },
  {
    id: "yaml_lab_result",
    label: "YAML records",
    inputFormat: "yaml",
    targetFormat: "json",
    schemaId: "lab_result_v1",
    instruction: "Validate these YAML lab records, convert them to JSON, and explain anomalies.",
    data: sampleYaml,
    fields: ["date", "patient_id", "lab_name", "value", "unit"],
  },
  {
    id: "fhir_observation",
    label: "FHIR Observation",
    inputFormat: "json",
    targetFormat: "json",
    schemaId: "",
    standard: "FHIR-like",
    instruction: "Profile this FHIR-like Observation, preserve the resource shape, and explain evidence.",
    data: sampleFhirObservation,
    fields: ["resourceType", "status", "code", "subject", "effectiveDateTime", "valueQuantity"],
  },
];
