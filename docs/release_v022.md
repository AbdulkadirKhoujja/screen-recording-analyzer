# v0.2.2: explicit pending-state quality gate

Date: 23 October 2026.

## Evidence received from the user's Windows machine

The user reported two successful Gemini 3.5 Flash-Lite multimodal calls on
synthetic mobile-app recordings. Task manager output identified four scripted
states, and the OCR stage-marker evaluator returned 4/4 within 1000 ms.
Tip calculator model output separately identified bill entry, tip selection,
processing/pending and a later $120.00 result. Its OCR marker evaluator again
returned 4/4 but flagged `uncertainty_flag_correct=false`. Inspection of the
provided analysis JSON showed a correctly worded pending *workflow step*, but
no separate `findings[].kind="uncertain"` entry. This is a model-format quality
failure, not failure to mention the processing screen. The $120 result is
supported by the later image and must not be backdated to the pending frame.

Those live Windows outputs were pasted into the conversation; they were **not
re-executed by the package builder or copied into this release**. User-reported
telemetry for the first request: input 4,546 tokens, output 738 tokens, 5,284
total tokens, 4 selected synthetic frames, `live_model_executed=true`. Actual
billed USD remains unknown. No customer footage was provided.

## Changes

- Strengthened the Gemini prompt to require an explicit cited `uncertain`
  finding whenever loading/processing is visible, even if later completed.
- Kept the returned model JSON untouched: the release does not auto-insert
  missing uncertain findings or award an artificial passing grade.
- Upgraded local evaluator with a second pending-state check and reporting
  gate, while preserving the existing OCR marker recall statistic.
- Fixed evaluator frame references to use ID lookups rather than array indexes.
- Switched the default requested model from unavailable Gemini 2.5 Flash to
  Gemini 3.5 Flash-Lite, observed working on user synthetic recordings.
- Added five local, no-network regression tests; 38 tests pass in clean-package
  checks, separate from any real model evaluation.

## Interpretation

Previously saved `outputs/tip-vision-flash-lite/analysis.json` is expected to
remain `uncertainty_flag_correct=false`, `pending_state_mentioned_in_workflow=true`,
`uncertainty_reporting_gate=REVIEW_REQUIRED`. This is the **correct honest
result for the original response**; the updated prompt requires a *future*
live response before claims of passing that gate.

The 8/8 combined result across two videos is a manual comparison of generated
workflow stage labels and controlled truth labels. The evaluator's own
`event_recall` is **OCR stage-marker detection**, not model semantic accuracy.
Sample size and content are too limited to demonstrate generalization.

## Follow-on release gates

- If the job is still available, verify terms, application status and proposal
  cost in a current authenticated Upwork view.
- One separately approved live inference could test whether the new prompt
  obtains an explicit uncertain finding; no automated calls run for this patch.
- Review and securely publish the independent self-directed GitHub portfolio
  demonstration, clearly marking synthetic limitations.
