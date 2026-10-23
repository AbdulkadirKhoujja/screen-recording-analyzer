# Public portfolio release review — 23 October 2026

## Scope and provenance

This is an **independent self-directed prototype**, not completed client work. This repository bundles the original synthetic recordings, generator/source code, frames and offline examples. A human ran Gemini on two of these known synthetic videos and reported the results; the live Google response files remain on the owner's Windows machine and **are not included in this public candidate**. The owner's release-review output still states `HUMAN_REVIEW_REQUIRED`. The synthetic stage markers are deliberately easy to read and should not be interpreted as a generalizable multimodal benchmark.

### Verified locally from packaged evidence

| Evidence | Result | Meaning / limitation |
| --- | --- | --- |
| Local regression suite | 46 passed | Local code/tests; does not certify external API availability |
| Synthetic videos | 2, each 8 seconds | Original demo apps, not real customers |
| OCR stage-marker detection | 8/8 within ±1 second | Visible scripted markers, **not model semantic accuracy** |
| Daymark steps (0/2/4/6s) | Four visible screen states | Empty list / task added / completed / completed filter |
| TipMate steps (0/2/4/6s) | Four visible screen states | Bill entry / tip selected / result pending / total displayed |
| TipMate pending distinction | Pending at 4s, $120 total at 6s | Different stages; 4s is **not** successful completion |

Video SHA-256: `todo_synthetic.mp4` = `7eb493caec0498f06eacd7a6f71f78765d4df17e8aa92d688f5e4a4810d95372`; `tip_synthetic.mp4` = `530d3dbfd03b77327c7e129aef5cc789b88623e7579da2b20fd1f73a355f1f8f`. These were computed from the distributed MP4 files.

### Owner-reported live Gemini observations (not independently replayed)

| Case | Model | Selected frames | Input/output/total tokens | Review outcome |
| --- | --- | ---: | --- | --- |
| Daymark | `gemini-3.5-flash-lite` | 4 | 4,546 / 738 / 5,284 | Four scripted states described, unsupported *single tap* phrase flagged |
| TipMate | `gemini-3.5-flash-lite` | 4 | 4,637 / 873 / 5,510 | Four scripted states described; explicit uncertain pending finding present; other capability claims flagged |

`live_model_executed=true` and `fallback_used=false` were present in the owner's reported run records. These recorded usage counts do **not** establish actual API billing or costs. The subsequent user's `release-review/live_evidence_review.md` returned `HUMAN_REVIEW_REQUIRED` for both cases. The owner reported a 38-test passing Windows run before these public documentation changes.

### Human review decisions for potentially unsupported text

| Raw model phrase | Judgment from bundled demo frames/source | Publication decision |
| --- | --- | --- |
| “single tap” | No measured tap count or interaction telemetry in selected frame evidence | Do not assert as verified |
| “processing payments” | Neither source app nor sampled screens implement or establish a payment flow | Do not assert |
| “bill splitting” | Appears as on-screen *promotional copy* (“Split every bill clearly”), not a demonstrated multi-payer feature | Describe as promotional text only |
| “instantly” | Processing/pending state visible and no measured timing claim; code schedules a later result | Do not assert instant completion |
| “total breakdown” | Only final total `$120.00` visible; no itemized breakdown demonstrated | Do not assert |

These decisions **annotate**, but do not modify, the underlying Gemini outputs. The built-in lexical detector is a conservative reviewer and may miss additional false or overstated claims.

### Acceptable portfolio claim

> A Python prototype that extracts evidence-linked frames and OCR from mobile screen recordings, produces structured workflow summaries, and optionally uses Gemini for visual interpretation. On two controlled original synthetic demos, the owner reported successful Gemini calls, while local OCR detected all eight scripted screen-state markers. The tool explicitly distinguishes uncertain states and flags unsupported claims for human review.

### Claims this repository does not establish

- Generalizable AI workflow accuracy, independent real-world test performance, or robust detection of every user action.
- Verified payment processing, bill splitting functionality, instant results, a particular number of taps, or total breakdown displays.
- Production readiness, verified client-specific acceptance, third-party privacy approval, or audited API charges.
- That the packaged *offline* examples are live Gemini output.

### Reproducing the review

Run `pytest -q` in a configured environment. Run the local OCR workflow in README without credentials or network. Owners who have their **own saved, unmodified live result folders** can run `review_release.py --todo ... --tip ... --out-dir release-review`; it performs no API requests and leaves original Gemini JSON untouched. The live folders are intentionally excluded by `.gitignore` and not shared in this repository.

Release assessment: **documentation suitable for a candid public portfolio; original model output and generalization claims remain HUMAN_REVIEW_REQUIRED**.
