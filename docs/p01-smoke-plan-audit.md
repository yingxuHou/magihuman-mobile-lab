# P01 Smoke Plan Audit

- Status: `ready`
- Manifest path: `docs/p01-smoke-manifest.json`
- Result dir: `outputs/smoke-test`

| Check | Status | Manifest | Plan |
| --- | --- | --- | --- |
| manifest_type | ok | `p01_smoke_input_manifest` | `p01_smoke_input_manifest` |
| case_id | ok | `P01` | `P01` |
| case_name | ok | `base_256p_t2v_smoke` | `base_256p_t2v_smoke` |
| mode | ok | `t2v` | `t2v` |
| resolution | ok | `256p` | `256p` |
| variant | ok | `base` | `base` |
| duration_seconds | ok | `5` | `5` |
| seed | ok | `42` | `42` |
| prompt_sha256 | ok | `8c18770e93a979ecf1c1d8b3f9d7d62e829bb0353118c3a48534891938218222` | `8c18770e93a979ecf1c1d8b3f9d7d62e829bb0353118c3a48534891938218222` |
| base_width | ok | `448` | `448` |
| base_height | ok | `256` | `256` |
| sr_width | ok | `null` | `null` |
| sr_height | ok | `null` | `null` |
| command | ok | `bash scripts/magihuman_task_runner.sh` | `bash scripts/magihuman_task_runner.sh` |
| expected_result_path | ok | `outputs/smoke-test/P01.mp4` | `outputs/smoke-test/P01.mp4` |
| env.MAGIHUMAN_TASK_ID | ok | `P01` | `P01` |
| env.MAGIHUMAN_PROMPT | ok | `A professional presenter looks at the camera and says hello to the audience in a calm voice.` | `A professional presenter looks at the camera and says hello to the audience in a calm voice.` |
| env.MAGIHUMAN_MODE | ok | `t2v` | `t2v` |
| env.MAGIHUMAN_RESOLUTION | ok | `256p` | `256p` |
| env.MAGIHUMAN_DURATION_SECONDS | ok | `5` | `5` |
| env.MAGIHUMAN_SEED | ok | `42` | `42` |
| env.MAGIHUMAN_MODEL_VARIANT | ok | `base` | `base` |
| env.MAGIHUMAN_RESULT_PATH | ok | `outputs/smoke-test/P01.mp4` | `outputs/smoke-test/P01.mp4` |
| env.MAGIHUMAN_MANIFEST_PATH | ok | `docs/p01-smoke-manifest.json` | `docs/p01-smoke-manifest.json` |
