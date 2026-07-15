# Stage 32: Evidence Package Provenance

Date: 2026-07-16

Status: complete for local tooling

## Goal

Make every GPU evidence package traceable to the code and source checkpoints that produced it.

The package manifest already rejects videos and model weights. Stage 32 adds provenance so the package also records:

- project Git commit and branch
- whether the project worktree was dirty during packaging
- official daVinci-MagiHuman source commit
- official MagiCompiler source commit
- P01 smoke manifest SHA-256

This matters because a runtime metrics JSON is not enough for the final mobile App decision unless we know which runner code, official source code, and P01 input contract produced it.

## Files Changed

| File | Purpose |
| --- | --- |
| `backend/evidence_provenance.py` | Builds JSON/Markdown provenance for GPU evidence packages |
| `scripts/package_gpu_evidence.sh` | Copies P01 manifest files and writes `evidence-provenance.json/md` before the package manifest |
| `tests/test_evidence_provenance.py` | Tests provenance generation and Markdown rendering |
| `tests/test_evidence_package.py` | Locks package script inclusion of P01 manifest and provenance files |

## Package Additions

`bash scripts/package_gpu_evidence.sh` now includes:

- `docs/p01-smoke-manifest.json`
- `docs/p01-smoke-manifest.md`
- `evidence-provenance.json`
- `evidence-provenance.md`

The package still excludes model weights and generated videos.

## Local Validation

Commands:

```powershell
python -m unittest tests.test_evidence_provenance tests.test_evidence_package -v
PACKAGE_DIR=outputs/test-evidence-provenance ARCHIVE_PATH=outputs/test-evidence-provenance.tar.gz bash scripts/package_gpu_evidence.sh
python -m unittest discover -s tests -v
python -m compileall backend tests
git diff --check
```

Result:

```text
Ran 120 tests
OK
Temporary evidence package manifest status: ok
Forbidden files: none
```

The temporary package was deleted after validation.

## Current Local Provenance

The local provenance command reports the current project commit at packaging time and verifies:

```text
daVinci-MagiHuman commit matches expected: true
MagiCompiler commit matches expected: true
P01 manifest exists: true
```

The worktree is dirty while this stage is being developed, which is expected before commit. On the GPU host, the provenance file will record whether the execution tree was dirty at packaging time.

## Next Step

After GPU execution, inspect `evidence-provenance.md` in the returned package before importing evidence. The official source commits should match the locked commits in this repo, and the P01 manifest hash should match the tracked `docs/p01-smoke-manifest.json` used by metrics context audit.
