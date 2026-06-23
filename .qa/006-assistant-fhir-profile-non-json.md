# QA Request: Assistant FHIR Profile Must Not Fail On Non-JSON Input

## Context

The Assistant planner may choose `fhir_profile` for user-provided medical text,
OCR output, CSV, or other non-JSON content. The runtime behavior should not mark
the tool as failed with `Invalid FHIR-like JSON` for non-JSON input.

## Required Checks

1. Send a plain-text assistant message that would previously trigger
   `fhir_profile`, for example:

   ```text
   HBA1C 7.4% FHIR OBS
   ```

2. Verify the `fhir_profile` tool result is `skipped`, not `failed`.

3. Verify the skipped result includes:

   - `code: FHIR_PROFILE_NOT_JSON`
   - no fabricated FHIR resource type;
   - no fake evidence;
   - `graphner_ready: false`.

4. Send malformed JSON beginning with `{` and verify the result is `skipped`
   with `code: FHIR_PROFILE_INVALID_JSON`, not a failed assistant run.

5. Send valid FHIR-like JSON, for example:

   ```json
   {"resourceType":"Observation","status":"final","code":{"text":"HbA1c"}}
   ```

   Verify `fhir_profile` still completes and returns profile evidence.

6. Verify the Assistant UI renders skipped FHIR profiling with a neutral/skipped
   badge, not a green completed badge and not a red failed badge.

7. Verify the live timeline does not leave `LLM text` in a running state after
   a stream error or cancel event.

## Non-Goals

This QA request does not prove FHIR conformance. It only verifies that the
Assistant does not hard-fail when FHIR profiling is not applicable.
