# P01 Smoke Input Manifest

| Field | Value |
| --- | --- |
| Status | `ready_for_gpu_execution` |
| Source commit | `209209b7086eba2020c5439265221495a8357322` |
| Case | `P01` / base_256p_t2v_smoke |
| Mode | `t2v` |
| Resolution | `256p` / 448x256 |
| Duration | 5 seconds |
| Seed | 42 |
| Prompt SHA-256 | `8c18770e93a979ecf1c1d8b3f9d7d62e829bb0353118c3a48534891938218222` |
| Reference image required | no |
| Expected result | `outputs/smoke-test/P01.mp4` |
| Metrics manifest path | `docs/p01-smoke-manifest.json` |
| Official script seconds | 4 |
| Official script base size | 448x256 |
| Official prompt file SHA-256 | `d175e0afe953de457a81f53f8f1fda5f43b0147fcca39c294b619d387a7c6229` |
| Official TI2V image SHA-256 | `0659ddf2d52dea107c8437889d850400929901676916ba3c5fe5feab4b116f65` |

P01 is a T2V smoke case, so it does not consume the official `example/assets/image.png` reference image. The image hash is still recorded for later TI2V cases.
