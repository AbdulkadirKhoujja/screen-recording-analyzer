# Screen Recording Analyzer — Evidence-First Prototype

**A transparent, runnable Python portfolio demonstration using entirely synthetic mobile-app footage. Not prior customer work, not a finished production AI analysis product.**

Two real local browser apps (a task tracker and a tip calculator) are exercised with Playwright and encoded as short MP4s. The tool extracts actual frames and timestamps, performs local Tesseract OCR, validates an auditable JSON schema, records uncertain states, and writes a readable Markdown review. A separately gated **Gemini image-keyframe integration was exercised by the user on two synthetic recordings** after the original offline demonstration; the original examples in this archive remain local OCR outputs. The user supplied the live structured results in chat, but their Windows output files are not bundled in this release. Live results are promising, not generalizable accuracy evidence.

## What this repository demonstrates

- **Reproducible local analysis:** frame extraction, timestamps, Tesseract OCR, strict Pydantic validation, and evidence-linked JSON/Markdown output.
- **Two original synthetic apps:** Daymark (task list → add → complete → filter) and TipMate (bill entry → tip selection → pending → total). In the controlled OCR benchmark, 8 of 8 displayed stage markers were detected within ±1 second; this is **not** a measure of AI semantic accuracy.
- **Opt-in Gemini image analysis:** the owner reported successful `gemini-3.5-flash-lite` API runs against both synthetic recordings on 23 October 2026, without fallback. The original remote output files are **not bundled here**, so this archive alone does not reproduce that remote success.
- **Human review remains required:** the owner's live-result review flags unsupported AI marketing/capability claims. Evidence references alone cannot prove semantic truth. See [public evidence review](docs/PORTFOLIO_RELEASE_REVIEW.md).
- **Automated regression tests:** 46 tests passed on the supplied v0.2.3 source in the release-review environment. An independent assessment with unfamiliar footage has not been performed.

[**View the synthetic example gallery**](examples/showcase.html) (download/open locally alongside its `examples/` image assets). No live Gemini call is needed to view it.

## Reproduce (Python 3.11+, ffmpeg/ffprobe and Tesseract installed)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test,demo]'
python demo/generate.py --out demo/assets
analyze demo/assets/todo_synthetic.mp4 --out outputs/todo --fps 2
analyze demo/assets/tip_synthetic.mp4 --out outputs/tip --fps 2
python evaluate.py outputs/todo demo/assets/todo_ground_truth.json
python evaluate.py outputs/tip demo/assets/tip_ground_truth.json
pytest -q
```

On Windows replace venv activation with `.venv\\Scripts\\activate`; install ffmpeg and Tesseract on PATH. The generator uses local Chromium at `/usr/bin/chromium` in this environment; adapt `executable_path` to your installed browser or use Playwright's managed browser. All videos and outcomes in `demo/assets/` are original synthetic test material.

## Outputs

- `frames.json` — video metadata, extracted images with exact sample positions and SHA-256 hashes.
- `ocr.json` — actual local OCR text, frame references and per-word confidence (>=50 retained).
- `analysis.json` — strict schema: app summary, time-labelled workflow screen states, time segments, marketing suggestions, observed/inferred/uncertain findings with frame IDs.
- `summary.md` — reviewable timeline and findings.
- `run.json` — actual source video hash, provider, runtime, frame count and model-usage fields. **Costs remain null for offline runs.**
- `evaluation.json` — ground-truth evaluation for stage labels (see below).

The offline output labels state changes from OCR and makes **no claim that it understands which button was pressed**. Two to three marketing suggestions are based on visible completion/result text and are clearly labelled **inferred**. A loading spinner is **uncertain** until an actual completed result appears. An observed finding needs a real evidence frame; however, **a citation does not itself verify semantic accuracy**.

## Measured synthetic test results

The included test runs generated two original 8-second portrait videos, containing four scripted states each. At sampling rate 2fps, the evaluator recovered **4/4 visible stage markers within ±1.0s on each video** and correctly identified the intentionally pending/uncertain state in the tip example. That is an **OCR marker detection metric on controlled synthetic videos**, not a general measure of workflow-understanding recall, ML precision, or performance on real client videos.

Both videos run through the *same code and configuration*, without hardcoded app names or ground-truth input to the analyzer. Evaluation against ground truth happens **after** the analysis completes.

## Optional multimodal Gemini (explicit opt-in)

```bash
pip install -e '.[live]'
export GOOGLE_API_KEY=your-own-key
analyze demo/assets/todo_synthetic.mp4 --out outputs/todo-vision \
  --provider gemini --model gemini-3.5-flash-lite --fps 1 \
  --allow-network --confirm-upload
```

This command deliberately uploads selected labelled screenshots to Google and **may incur charges** depending on the account/tier. Never upload confidential client recordings to a free-tier service without specific data-processing approval; Google currently notes different training/data-use terms for its free versus paid tiers. The external vision path was subsequently exercised by the user on synthetic footage: both calls returned structured results using `gemini-3.5-flash-lite`. The user-reported live results are not bundled as reproducible local files; actual charges and generalized accuracy are not established. The `google-genai` package and a private user-supplied API key are required. No key is included.

The current default model ID `gemini-3.5-flash-lite` is the model reported working in the user's October 2026 synthetic test, not a promise about future availability, account eligibility or pricing. Before deploying, verify current model selection, supported SDK schema and up-to-date fees using Google's [official pricing](https://ai.google.dev/gemini-api/docs/pricing), [video understanding](https://ai.google.dev/gemini-api/docs/video-understanding) and [SDK documentation](https://googleapis.github.io/python-genai/). Input/output token usage is recorded if the provider returns it; **no claimed dollar estimate is produced without an agreed and current price table**. Gemini is swappable in the code, but **no Claude provider implementation or provider interchange benchmark has been claimed**.

## Boundaries / acceptance

- Applies to short videos up to 180s and 3840×2160, with a configured cap on sampled frames (default 120, maximum 48 for Gemini upload). Fast UI interactions may be missed at 1fps. No audio transcription.
- Gemini-generated JSON is schema checked and evidence frame references and timestamp bounds verified, but semantic correctness still needs a separate human evaluation against ground truth.
- Synthetic tests contain no customer footage, uploads, payments, API spending or secret keys.
- Not ready to claim that it fully meets a customer's multimodal-vision acceptance requirement. Live opt-in calls on the two known synthetic videos have been user-reported, but a genuinely unfamiliar client-approved video test, independent semantic accuracy evaluation and data/privacy approval are still necessary.
- This demonstration does not authorise any external customer data processing or submissions.

## Project structure

```
src/screen_analyzer/  Python CLI, frame extraction, strict schemas, providers
demo/                 Two self-contained synthetic interactive HTML apps
                       Playwright screenshots, ffmpeg recording generator
demo/assets/          Two generated synthetic MP4s + ground truth (not customer footage)
tests/                Real pytest regression tests
evaluate.py           Compares OCR marker observations against logged stage changes
examples/             Genuine output from local offline runs
```

This demonstration is original self-directed portfolio work. Do not describe it as commissioned customer work or upload confidential source/video data.

## Release v0.2 — tested provider routing (22 October 2026)

The original OCR prototype remains the default with **no external calls**. Version 0.2 adds an explicit preflight, opt-in Gemini-to-offline fallback, caller-supplied rate assumptions for estimates, and regression tests for both provider routes. A fallback response is **not** presented as a successful Gemini execution.

```bash
# Safe: provider configuration check only, no video read or upload
analyze --provider offline-ocr --preflight-only

# Only if you have your own key and expressly accept the vendor's data terms:
analyze --provider gemini --model gemini-3.5-flash-lite --preflight-only \
  --allow-network --confirm-upload

# Safe: offline real local video run
analyze demo/assets/todo_synthetic.mp4 --out outputs/todo --fps 2

# Only if authorised: remote Gemini call with explicit, logged fallback
analyze demo/assets/todo_synthetic.mp4 --out outputs/todo-vision \
  --provider gemini --model gemini-3.5-flash-lite --fps 2 \
  --allow-network --confirm-upload --fallback-offline
```

A Gemini route with missing credentials fails **before producing output**, unless explicit fallback is enabled with the two consent flags; then OCR runs and `run.json` reports the actual executed provider plus the fallback reason. Network attempts that fail may still incur charges. Fallback is never enabled silently.

For an *estimate* after actual model usage is returned, pass both `--input-usd-per-million` and `--output-usd-per-million`, with values checked against official pricing **for your actual model, tier, date and request type**. For example, a purely hypothetical rate pair `0.30`/`2.50` is used in tests, but these are **not** asserted to be current prices. Report fields separate `model_call_attempted`, `live_model_executed`, `provider`, `requested_provider`, and `estimated_api_cost_usd`. Estimates do not prove an amount was billed.

**Evidence:** v0.2 includes 31 passing local automated tests, two real synthetic-video OCR runs, and 8/8 controlled marker detections with ±1-second tolerance. This is *not* an independent live vision-model test. Gemini SDK behavior remains mocked; a live model key, provider approval and independent semantic evaluation are required for that claim. Current free-tier data terms may permit submitted content to improve Google products; verify the provider's official terms before any personal or customer footage upload.

For release evidence see `docs/release_v02.md` and `verification.json`.


## Patch v0.2.1 — Gemini structured output schema (23 October 2026)

A live user-authorized synthetic-video attempt returned HTTP 400 `INVALID_ARGUMENT`
with `Unknown name "additional_properties"` inside
`generation_config.response_schema`. The existing Pydantic `extra="forbid"`
model's schema was converted by the SDK into the older `response_schema`
wire representation, which does not accept these nested fields.

We now pass `response_json_schema=Analysis.model_json_schema()` instead of
`response_schema=Analysis` and retain strict client-side
`Analysis.model_validate_json(response.text)` validation. This follows
Google GenAI SDK's documented JSON Schema option and preserves Pydantic
`additionalProperties: false` restrictions. The adapter is unit-tested with
a mocked SDK; this patch does **not** assert a successful remote call. Run a
consented synthetic-video live validation to confirm end-to-end service behavior.

See: https://googleapis.github.io/python-genai/genai.html

## Release v0.2.2 — explicit pending-state reporting (23 October 2026)

The first consented live Gemini calls against original synthetic Task Manager and
TipMate recordings returned structured results through `gemini-3.5-flash-lite`.
Both model-generated step lists matched the four scripted screen states in a
manual review. This **does not establish generalized model accuracy**.

The TipMate response correctly described a processing/pending state in its
workflow steps but omitted a separate `kind="uncertain"` finding. The existing
synthetic OCR evaluator therefore correctly returned
`"uncertainty_flag_correct": false`. Version 0.2.2:

- Requires explicit uncertain findings for in-progress states in the Gemini
  **prompt**, preserving later confirmed results without rewriting history.
- Separately reports `pending_state_mentioned_in_workflow` and
  `uncertainty_reporting_gate` (`PASS`, `REVIEW_REQUIRED`, or `NOT_APPLICABLE`).
- Uses frame IDs rather than array offsets for uncertainty evidence checks.
- Adds four offline regression tests; **does not modify historical live model
  output** or fabricate any result.

Run the evaluation again on an existing saved live output, without API calls:

```bash
python evaluate.py outputs/tip-vision-flash-lite demo/assets/tip_ground_truth.json
```

Existing live TipMate output should remain `REVIEW_REQUIRED` until a future
model response itself includes the correctly cited explicit uncertain finding.
A clean local test result is not evidence that the new prompt has already been
validated against a real model. Live calls require explicit network/upload
consent and may be chargeable depending on the account tier.

## v0.2.3 — local live-result quality review (23 October 2026)

Version 0.2.3 adds a conservative, **non-destructive lexical claim-review gate** and an offline evidence collector that checks live execution provenance against the original synthetic video hashes. It flags potentially unsupported statements rather than altering the model's response or claiming to verify visual truth. Eight new no-network regression tests bring the locally verified suite to **46 tests**.

To review your *existing* Gemini output folders (no key, upload or model call required):

```powershell
& .\.venv\Scripts\python.exe .\review_release.py `
  --todo .\outputs\todo-vision-flash-lite `
  --tip .\outputs\tip-vision-v022-live `
  --out-dir .\release-review
Get-Content .\release-review\live_evidence_review.md
```

Both generated files remain **local** and are excluded from version control until inspected. `HUMAN_REVIEW_REQUIRED` is the intentional publication status; an apparently clean scan is not an independent semantic benchmark. See [`docs/release_v023.md`](docs/release_v023.md).
