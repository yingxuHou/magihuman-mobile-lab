# Stage 17: Quality Review Gate

Date: 2026-07-16

Status: complete for local tooling

## Goal

Add a structured quality review gate before the mobile feasibility decision can move from measured runtime data to a product recommendation.

Runtime metrics alone can prove that a GPU host produced files, but they do not prove that the generated samples are acceptable for a phone app. The final app decision needs review evidence for playback, lip sync, face quality, motion naturalness, speech intelligibility, and visible artifacts.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/quality_review.py` | Creates quality review templates and summarizes completed reviews |
| `tests/test_quality_review.py` | Tests template generation, missing review files, passing reviews, failed reviews, and incomplete reviews |
| `backend/feasibility_decision.py` | Uses optional quality review evidence before advancing the cloud route |
| `scripts/quality_review.ps1` | Windows launcher |
| `scripts/quality_review.sh` | Linux launcher |
| `docs/quality-review-rubric.md` | Human review rubric and commands |
| `scripts/gpu_reproduction_pipeline.sh` | Accepts `QUALITY_REVIEW=<path>` for final feasibility decisions |

## Quality Review Template

Create a template:

```powershell
python -m backend.quality_review --create-template --output docs/quality-review.json
```

Required cases:

- P01
- P03
- P04
- T01
- T02

Each case records:

- `playable_on_phone`
- `audio_video_sync_score`
- `face_quality_score`
- `motion_naturalness_score`
- `speech_intelligibility_score`
- `artifact_free_score`
- `notes`

Scores use a 1 to 5 scale. The minimum passing score is 3.

## Feasibility Decision Integration

Current command without a review file:

```powershell
python -m backend.feasibility_decision --log-dir logs --format markdown
```

Current output still remains:

```text
Recommendation: B_pending_runtime
Quality Evidence: missing_quality_review
```

After GPU metrics exist, the cloud route can only move to:

- `B_candidate_needs_quality_review` if no completed review exists
- `B_candidate_needs_cost_review` if required samples pass review
- `C_candidate_quality_failed` if required samples fail review

Stage 18 adds the next required gate after quality: cost and wait-time review.

## GPU Pipeline Integration

After filling a review file:

```bash
QUALITY_REVIEW=docs/quality-review.json EXECUTE=1 bash scripts/gpu_reproduction_pipeline.sh
```

The generated feasibility report will include quality evidence.

## Validation

Command:

```powershell
python -m unittest tests.test_quality_review tests.test_feasibility_decision -v
```

Result:

```text
Ran 10 tests
OK
```

## Next Step

After GPU outputs are produced, fill `docs/quality-review.json`, rerun the quality review summary, then rerun the feasibility decision with `--quality-review`.
