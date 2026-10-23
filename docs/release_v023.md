# v0.2.3 — evidence-quality review and offline live-run provenance

Date: 23 October 2026. Independent synthetic portfolio demonstration, **not commercial client delivery**.

## What this update changes

1. The opt-in Gemini system prompt now distinguishes **on-screen promotional copy** from proof that a capability functions. It discourages unsupported claims such as payment processing, multi-payer bill splitting, instant timing, total breakdowns or exact tap counts.
2. `screen_analyzer.claim_review.review_claims()` scans model-produced text for **potential** capability, performance or interaction overclaims. It returns flags for human judgment; it never edits or hides the model's original answer. A clean lexical scan is not a semantic verification pass.
3. `review_release.py` reads the user's two **already saved** live Gemini result folders. It verifies local Pydantic validity, frame references, original synthetic source hashes, true Gemini execution (not fallback), ground-truth *OCR marker* scores and uncertainty-gate status. It writes a compact, reviewable local JSON and Markdown summary, without network calls, model inference or a new Google API request.
4. A local release gate remains `HUMAN_REVIEW_REQUIRED`. This tool cannot certify model accuracy, infer what happened between sampled frames, or authorise client-data processing.

## Collect existing Windows evidence

From the existing project directory, with the virtual environment's Python:

```powershell
& .\.venv\Scripts\python.exe .\review_release.py `
  --todo .\outputs\todo-vision-flash-lite `
  --tip .\outputs\tip-vision-v022-live `
  --out-dir .\release-review

Get-Content .\release-review\live_evidence_review.md
```

This **does not** reveal or access the Google API key, or upload videos. Original model output stays unchanged. If input is missing, a fallback was used, or the recorded video hash differs from the packaged originals, collection fails rather than claiming a positive live result. Review the `release-review` files before any public sharing; the folder is excluded from Git by default.

## Evidentiary distinction

- The owner reported 38 passing Windows tests of v0.2.2 on 23 October 2026, plus successful live Gemini responses on the two original synthetic videos. The current update was built and locally tested separately; we have **not** independently rerun the user's connected Google API calls.
- Four scripted states per video are apparent in supplied generated workflow descriptions; the automated `event_recall` metric still scores OCR marker detection rather than AI semantic accuracy.
- The most recent TipMate `analysis.json` pasted by the owner contains an explicit `uncertain` finding for the 4000 ms pending frame, but the corresponding current evaluator output has not yet been submitted. The offline collector measures it against the saved file.
- Supported claims and marketing copy require human review, even with correct frame references.
- Billing remains unknown without authoritative account billing data. Tokens are usage evidence, not prices.
- Current Upwork job availability and proposal cost remain unverified. No proposal submission or publication is part of this release.
