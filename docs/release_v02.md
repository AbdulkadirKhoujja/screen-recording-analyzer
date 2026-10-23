# v0.2 release verification / evidence limits

## Change summary

- Restored original 0.1.0 verified artifact, checked all original file hashes, reran original 17 tests.
- Added `screen_analyzer.routing.preflight` for provider authorization and SDK availability without an API request.
- Added explicit fallback to OCR with requested/executed provider distinction and visible reason; no silent fallback.
- Added `--preflight-only`, `--fallback-offline`, and operator-supplied input/output rates; no price claims by default.
- Added success, failure, consent, missing-key, fallback, and pricing route tests.
- Retested both original synthetic videos and the original ground-truth scorer after changes.

## Attestation scope

- Local test pass proves the Python implementation and output contracts in this environment only.
- Gemini contract and cost tests are mocks. They do **not** prove a real response, model classification accuracy, remote schema compatibility, or billing.
- OCR ground truth measures detection of deliberately displayed state markers at 0, 2, 4 and 6s (per app) within ±1s.
- Model upload has never been authorised and no Gemini credential has been supplied in this runtime.
- No customer assets, Upwork account actions or paid operations were needed.
- `fallback_offline` is not a privacy control once remote execution has begun. Even if a remote call fails, frames may have been transmitted and provider-side charges can occur.
- Pricing source for a real run: https://ai.google.dev/gemini-api/docs/pricing. Verify current rates at execution time.

## Future acceptance gates

1. Obtain explicit approval, a separate test key, confirmed privacy terms and a spending limit before attempting live synthetic Gemini footage.
2. Measure independently labelled semantic workflow understanding on recordings not used to devise test markers.
3. Recheck the Upwork job's exact live availability and proposal cost before submission.
4. Publish public MIT repository only after a final privacy/source review; portfolio must be called independent self-directed work.


## 0.2.1 compatibility patch (23 October 2026)

- User-reported live attempt: Gemini returned HTTP 400 INVALID_ARGUMENT with
  `Unknown name additional_properties` from `generation_config.response_schema`.
- Changed only the provider's structured response argument from the older
  `response_schema=Analysis` to `response_json_schema=Analysis.model_json_schema()`.
- Strict local Pydantic validation is retained; explicit opt-in, user-key
  handling, frame limits, and cost semantics are unchanged.
- Added regression tests verifying JSON Schema routing and strict validation.
- New live model success not yet attested; server compatibility cannot be
  proven by SDK mocks alone.
