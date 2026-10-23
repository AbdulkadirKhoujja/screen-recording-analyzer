> **Historical baseline note:** this document describes the initial offline proof. For the later owner-reported live Gemini runs and limits, see [the public portfolio review](PORTFOLIO_RELEASE_REVIEW.md).

# Technical decisions, reproducibility and remaining acceptance gaps

## What was executed

- Two synthetic self-contained local web apps were exercised using Chromium/Playwright and encoded as fixed-rate MP4 footage with ffmpeg.
- Both MP4s were decoded with OpenCV; ffprobe inspected dimensions, rate and duration; selected frames were saved with presentation timestamps and SHA-256 hashes.
- Local Tesseract OCR read the actual pixels (without any model API); a heuristic distinct-state extractor produced structured, strictly validated output and referenced frame IDs.
- An independent evaluator used the **separately generated** script ground truth to score only visual stage-text marker recall and timing. It did not score complete semantic application understanding.
- Python automated tests were genuinely executed and recorded in `test_results.txt`.
- The Gemini image-keyframe adapter was tested with a **mocked SDK client and synthetic response only**. No live model accuracy, response format guarantees on the real remote service, prompt robustness, token-based billing or cost claims have been established.

## Intentional divergences from the aspirational design brief

- This prototype uses OpenCV decoded-frame sampling and pixel-difference scene detection. It does not yet implement ffmpeg's `select=gt(scene,T)`/`showinfo` indexing or compare against VFR subtitle timings.
- The offline provider is OCR-only, not a multimodal language model. The actual app summary is labelled an OCR preview rather than an invented semantic summary.
- Per-run API costs are `null` unless a real live provider call and current price schedule are verified. No paid calls were made.
- No Claude provider is wired; Gemini is an optional explicit-consent path, not a verified interchangeable production backend.
- Mocked provider tests prove only local request/payload/schema wiring; not correctness of Google's current hosted interface.
- Ground truth comes from script state markers and does not validate every inferred step or all potential marketing moments.
- The browser video generator reconstructs exact synthetic stages from Playwright screenshots. The timestamps are the known encoded-frame positions, not real-time measured human interaction latency.
- Long recordings, fast taps, audio, confidential videos, production schema tuning and Windows-specific packaging have not been independently validated.

## External official references checked for architecture, not pricing claims

- https://ai.google.dev/gemini-api/docs/video-understanding — describes default 1 fps video input and risks of missing rapid changes.
- https://ai.google.dev/gemini-api/docs/pricing — model availability and fees; free tier may permit content to improve Google products, paid tier differs. Model pricing can change.
- https://googleapis.github.io/python-genai/ — SDK request and response structures.

This is a self-directed synthetic engineering demonstration, not prior commercial delivery. Do not upload client recordings to external providers or call the integration production-ready without additional agreement and tested evidence.
