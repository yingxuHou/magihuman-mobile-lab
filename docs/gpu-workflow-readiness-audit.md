# GPU Workflow Readiness Audit

- Status: `ready`
- Project root: `.`

| Check | Status | Detail |
| --- | --- | --- |
| workflow script exists | ok | scripts/run_gpu_reproduction_workflow.sh |
| workflow runs upstream drift audit strictly | ok | upstream drift audit before GPU work |
| workflow prepares locked sources | ok | locked source preparation is present |
| workflow order is P01 before full suite before package | ok | P01-first execution order |
| workflow forces P01 execution | ok | P01 pipeline executes with p01 profile |
| workflow forces required-suite execution | ok | full pipeline executes with required_suite profile |
| workflow disables nested source prep | ok | pipelines do not repeat source preparation |
| P01 pipeline has strict acceptance gate | ok | P01 acceptance blocks full suite |
| full pipeline has strict required-suite gate | ok | required-suite acceptance blocks quality/cost review |
| package includes P01 acceptance JSON | ok | P01 gate evidence enters package |
| package includes required-suite acceptance JSON | ok | full-suite gate evidence enters package |
| bootstrap execute mode uses workflow | ok | gpu_bootstrap execute path |

The GPU reproduction workflow is ready to run on a prepared GPU host.
