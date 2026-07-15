# Stage 30: Metrics Run Context

Date: 2026-07-16

Status: complete for local tooling

## Goal

Make every GPU metrics JSON self-identifying.

Before this stage, `logs/*_metrics.json` captured timing, GPU, and video metadata, but it did not record which planned case produced the file or which seed, prompt, target duration, target resolution, and manifest were used. That made the post-GPU evidence audit depend on filenames and shell logs.

Stage 30 adds run context metadata directly to metrics JSON so P01 and the later required-suite cases can be matched to the planned experiment matrix.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/run_metrics.py` | Adds optional run-context fields and manifest hashing |
| `scripts/magihuman_task_runner.sh` | Passes case id, mode, resolution, variant, seed, duration, target size, result path, prompt hash source, and optional manifest path to `run_metrics` |
| `backend/experiment_matrix.py` | Adds `MAGIHUMAN_MANIFEST_PATH=docs/p01-smoke-manifest.json` for P01 |
| `docs/p01-smoke-manifest.json` | Regenerated so P01 runner env includes the manifest path |
| `tests/test_run_metrics.py` | Covers run-context metadata and manifest hash capture |

## Metrics Shape

Future GPU metrics JSON can now include:

```json
{
  "run": {
    "case_id": "P01",
    "mode": "t2v",
    "resolution": "256p",
    "variant": "base",
    "seed": 42,
    "target_duration_seconds": 5.0,
    "target_br_width": 448,
    "target_br_height": 256,
    "result_path": "outputs/smoke-test/P01.mp4",
    "prompt_sha256": "...",
    "manifest_path": "docs/p01-smoke-manifest.json",
    "manifest_sha256": "..."
  },
  "time": {},
  "gpu": {},
  "video": {}
}
```

The existing `time`, `gpu`, and `video` sections are unchanged, so previous summary tools remain compatible.

## Validation

Commands:

```powershell
python -m unittest tests.test_run_metrics tests.test_experiment_matrix tests.test_smoke_manifest -v
python -m unittest discover -s tests -v
python -m compileall backend tests
git diff --check
```

Result:

```text
Ran 112 tests
OK
```

## Next Step

After P01 runs on the GPU host, inspect `logs/*P01*_metrics.json` and confirm:

- `run.case_id` is `P01`
- `run.seed` is `42`
- `run.target_duration_seconds` is `5.0`
- `run.target_br_width`/`run.target_br_height` are `448`/`256`
- `run.manifest_path` is `docs/p01-smoke-manifest.json`
