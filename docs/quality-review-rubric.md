# Quality Review Rubric

Use this rubric after GPU inference produces P01, P03, P04, T01, and T02 samples.

Create a review template:

```bash
python -m backend.quality_review --create-template --output docs/quality-review.json
```

Fill every required case in the JSON file, then summarize:

```bash
python -m backend.quality_review --review docs/quality-review.json --format markdown
```

Feed the completed review into the feasibility decision:

```bash
python -m backend.feasibility_decision --log-dir logs --quality-review docs/quality-review.json --format markdown
```

## Required Cases

| Case | Review Focus |
| --- | --- |
| P01 | 256p baseline: playable output, audio presence, basic face/motion quality |
| P03 | 540p SR: quality improvement without severe artifacts |
| P04 | 1080p SR: final presentation quality and artifact level |
| T01 | Mandarin TI2V: speech intelligibility and audio-video sync |
| T02 | English TI2V: speech intelligibility and audio-video sync |

## Score Scale

| Score | Meaning |
| ---: | --- |
| 1 | Unusable |
| 2 | Poor |
| 3 | Demo acceptable |
| 4 | Good |
| 5 | Excellent |

Minimum passing score: 3.

## Fields

Each case must include:

- `playable_on_phone`: `true` only if the sample plays correctly on a real phone
- `audio_video_sync_score`
- `face_quality_score`
- `motion_naturalness_score`
- `speech_intelligibility_score`
- `artifact_free_score`
- `notes`

The final feasibility decision will not advance past `B_candidate_needs_quality_review` until all required cases pass this review.
