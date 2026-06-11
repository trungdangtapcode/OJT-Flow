# OCR Evidence UI v0

## Scope

The OCR evidence UI is a review surface for structured OCR output. It does not
run OCR by itself. It accepts page/field/value/bounding-box/confidence records,
normalizes them through `POST /api/v1/ocr/evidence`, and renders the backend
response for human review.

This keeps responsibilities separated:

- OCR engines produce field candidates.
- `MedicalEvidenceService.normalize_ocr_evidence` applies the backend evidence
  contract and review threshold.
- The Workbench UI groups normalized fields by page and shows confidence,
  source refs, bounding boxes, and evidence IDs.

## Input Shape

The Workbench panel accepts either a JSON array or an object with a `fields`
array:

```json
{
  "fields": [
    {
      "page": 1,
      "name": "field_name",
      "value": "extracted value",
      "bbox": [72, 144, 96, 18],
      "confidence": 0.95,
      "source_ref": "storage://artifact/page-1",
      "normalized_to": null
    }
  ]
}
```

`bbox` is `[x, y, width, height]` in source coordinates. The UI scales these
coordinates into a page map for review; it does not assume a fixed page size.

## Output Review

The normalized response contains:

- `fields`: backend-assigned `field_id`, confidence, page, bbox, source ref, and
  `requires_review`.
- `evidence`: one `ocr_box` evidence item per normalized field.
- `requires_review`: true if any field confidence is below the backend threshold.

The UI groups fields by `page`, marks low-confidence fields, shows the source
reference, and keeps the evidence IDs visible for audit handoff.

## Verification

1. Open Workbench.
2. Paste OCR field JSON into the OCR evidence review panel.
3. Click `Normalize OCR evidence`.
4. Confirm the panel renders one section per page.
5. Confirm low-confidence fields are marked for review.
6. Confirm evidence IDs and source refs are visible.

The implementation is verified by the frontend build and existing OCR endpoint
API tests. Full OCR engine integration remains separate Month 2/Month 3 work.
