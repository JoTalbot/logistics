# Remote-Agent Command Policy Audit — 2026-09-17

## Scope

Audit the autonomous command surface of the remote control plane, with emphasis on whether `AUTO` classification can escape the intended workspace boundary or turn argument handling into an unintended privilege path.

## Findings

### 1. Authentication and dispatch boundary

The control plane requires the operator credential to create tasks. The agent only polls tasks classified as `AUTO`; `REVIEW` and `BLOCK` tasks are not dispatched by the autonomous polling endpoint.

### 2. Shell composition

The classifier rejects shell composition tokens (`&&`, `||`, `;`, `|`, redirection, backticks and command substitution) before parsing. Existing regression coverage also checks representative composed commands and Python `-c` execution.

### 3. Current AUTO argument boundary

The current classifier accepts any command beginning with `python -m pytest` or `python -m compileall` as `AUTO`, because it checks only the first three parsed argv elements. This leaves an argument-level policy gap: absolute paths or `..` traversal can still be supplied after those prefixes.

The remote agent separately confines its `cwd` to the configured workspace, but that does not constrain file/path arguments passed to Python tooling. Therefore the workspace policy is stronger for `cwd` than for AUTO command arguments.

### 4. Risk assessment

This is a policy-hardening issue, not evidence of an unauthenticated remote execution path. The autonomous surface is already narrower than the direct authenticated `/v1/exec` administrative endpoint, and the service runs under the dedicated non-root identity. Nevertheless, AUTO classification should not rely on a command prefix when the remaining arguments can select filesystem paths or Python/pytest configuration outside the workspace.

## Required hardening

Before expanding autonomous execution, change `_approval()` so AUTO Python tooling validates all arguments:

- reject absolute paths;
- reject path components containing `..`;
- reject pytest options that load external plugins/configuration or otherwise redirect discovery outside the workspace;
- preserve existing safe relative test/module paths and simple flags such as `-q`;
- keep non-conforming commands at `REVIEW` rather than attempting string-prefix inference.

Add regression coverage for at least:

- `python -m compileall /tmp` -> `REVIEW`;
- `python -m compileall ../outside` -> `REVIEW`;
- `python -m pytest /tmp/test_x.py` -> `REVIEW`;
- `python -m pytest ../outside` -> `REVIEW`;
- `python -m pytest -q` -> `AUTO`;
- `python -m pytest tests/test_remote_control.py` -> `AUTO`;
- external pytest plugin/configuration selectors -> `REVIEW`.

## Execution state

The current ChatGPT execution surface can inspect and commit repository files through GitHub but cannot execute the repository locally. The existing CI evidence therefore remains the authoritative execution evidence until a fresh workflow run verifies the hardening.

This audit does not activate runtime cgroup enforcement and does not weaken the existing fail-closed target-host rehearsal gate.
