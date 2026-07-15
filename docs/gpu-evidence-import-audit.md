# GPU Evidence Import Audit

Status: `incomplete_import`

Final report status: `incomplete_runtime_evidence`

Recommendation: `B_pending_runtime`

## Inputs

| Input | Path |
| --- | --- |
| log_dir | logs |
| quality_review | - |
| cost_review | - |
| final_report_output | docs\mobile-feasibility-report.md |

## Gate Statuses

| Gate | Status |
| --- | --- |
| Static on-device feasibility | `not_viable` |
| Required GPU runtime metrics | `insufficient_runtime_evidence` |
| Generated sample quality | `missing_quality_review` |
| Cloud GPU cost and wait time | `missing_cost_review` |
| Mobile video playback compatibility | `missing_mobile_video_evidence` |

## Missing Evidence

| Gate | Items | Action |
| --- | --- | --- |
| runtime | P01, P03, P04, T01, T02 | Import logs/*_metrics.json from the GPU host for the missing cases. |
| quality | missing_quality_review | Import or complete docs/quality-review.json. |
| cost | missing_cost_review | Import or complete docs/cost-review.json. |
| mobile_video | P01, P03, P04, T01, T02 | Import metrics JSON with ffprobe video metadata for generated samples. |

## Current Final Report

### Final Mobile Feasibility Report

Status: `incomplete_runtime_evidence`

Recommendation: `B_pending_runtime`

#### Executive Summary

- Official on-device inference is `not_viable`.
- Cloud backend route is `pending_runtime_evidence`.
- Stop/productization route is `not_decided`.

#### Evidence Gates

| Gate | Status | Summary |
| --- | --- | --- |
| Static on-device feasibility | `not_viable` | Official on-device stack is rejected by size, CUDA dependency, and missing mobile export path. |
| Required GPU runtime metrics | `insufficient_runtime_evidence` | Required GPU metrics are missing: P01, P03, P04, T01, T02 |
| Generated sample quality | `missing_quality_review` | No quality review file was provided. |
| Cloud GPU cost and wait time | `missing_cost_review` | No cost review file was provided. |
| Mobile video playback compatibility | `missing_mobile_video_evidence` | Mobile playback evidence is missing for required cases: P01, P03, P04, T01, T02 |

#### Decision

##### Mobile Feasibility Decision

Recommendation: `B_pending_runtime`

| Option | Track | Status | Evidence |
| --- | --- | --- | --- |
| A | Official on-device inference | `not_viable` | Complete official checkpoint stack is about 285.63 GiB before cache, logs, and outputs. |
| B | Mobile app plus cloud GPU backend | `pending_runtime_evidence` | Backend API, worker, runner, metrics, retry, and retention prototypes exist locally. |
| C | Stop app productization | `not_decided` | Stopping productization would be premature before cloud GPU runtime data is collected. |

###### Static Evidence

- Complete checkpoint stack: 285.63 GiB
- Base smoke-test dependency footprint: 114.64 GiB
- Official mobile export path found: no
- Requires CUDA GPU runtime: yes

###### Runtime Evidence

- State: `insufficient_runtime_evidence`
- Required cases: P01, P03, P04, T01, T02
- Measured required cases: none
- Missing required cases: P01, P03, P04, T01, T02

###### Quality Evidence

- State: `missing_quality_review`
- Summary: No quality review file was provided.
- Review file: -

###### Cost Evidence

- State: `missing_cost_review`
- Summary: No cost review file was provided.
- Review file: -

###### Next Required Actions

- Run missing required experiment cases on a Linux NVIDIA GPU host: P01, P03, P04, T01, T02.
- Collect metrics JSON files with wall time, peak VRAM, video metadata, and audio presence.
- Review generated samples on mobile devices for playback, quality, and share/save behavior.

#### Runtime Metrics

| ID | Status | Resolution | Mode | GPU | Wall time (s) | Peak VRAM (MiB) | Video | Audio | Metrics |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| P01 | missing_metrics | 256p | t2v | - | - | - | - | - | - |
| P02 | missing_metrics | 256p | t2v | - | - | - | - | - | - |
| P03 | missing_metrics | 540p | t2v | - | - | - | - | - | - |
| P04 | missing_metrics | 1080p | t2v | - | - | - | - | - | - |
| T01 | missing_metrics | 256p | ti2v | - | - | - | - | - | - |
| T02 | missing_metrics | 256p | ti2v | - | - | - | - | - | - |
| T03 | missing_metrics | 256p | ti2v | - | - | - | - | - | - |
| T04 | missing_metrics | 256p | ti2v | - | - | - | - | - | - |

#### Quality Review

##### Quality Review

- Status: `missing_quality_review`
- Summary: No quality review file was provided.
- Review file: -

| Case | Status | Sample | Missing | Invalid | Failed |
| --- | --- | --- | --- | --- | --- |
| - | `missing_quality_review` | - | - | - | - |

#### Cost Review

##### Cost Review

- Status: `missing_cost_review`
- Summary: No cost review file was provided.
- Review file: -

| Case | Status | Wall time (s) | Cost/video | Cost status | Latency status |
| --- | --- | ---: | ---: | --- | --- |
| - | `missing_cost_review` | - | - | - | - |

#### Mobile Video Compatibility

##### Mobile Video Compatibility

- Status: `missing_mobile_video_evidence`
- Source: logs

| Case | Status | Metrics | Failed checks | Transcode command |
| --- | --- | --- | --- | --- |
| P01 | `missing_video_metrics` | - | - | - |
| P03 | `missing_video_metrics` | - | - | - |
| P04 | `missing_video_metrics` | - | - | - |
| T01 | `missing_video_metrics` | - | - | - |
| T02 | `missing_video_metrics` | - | - | - |
