# Remote-Agent Command Policy Audit — 2026-09-17

## Scope

Audit the autonomous command surface of the remote control plane, with emphasis on whether `AUTO` classification can escape the intended workspace boundary or turn argument handling into an unintended privilege path.

## Findings

### 1. Authentication and dispatch boundary

The control plane requires the operator credential to create tasks. The agent only polls tasks classified as `AUTO`; `REVIEW` and `BLOCK` tasks are not dispatched by the autonomous polling endpoint.

### 2. Shell composition

The classifier rejects shell composition tokens (`&&`, `||`, `;`, `|`, redirection, backticks and command substitution) before parsing. Existing regression coverage also checks representative composed commands and Python `-c` execution.

### 3. AUTO argument boundary

The Python AUTO policy now validates every argument rather than trusting only the `python -m pytest` / `python -m compileall` prefix. Absolute paths, backslash-containing paths and lexical `..` traversal are rejected. Pytest plugin/configuration and arbitrary option injection are rejected; only a small explicit set of bounded flags is accepted. Safe relative workspace paths remain supported.

The remote agent separately confines its `cwd` to the configured workspace. The two controls therefore provide defense in depth: control-plane AUTO classification limits the command language, while the agent independently validates the executable and cwd before spawning.

### 4. Risk assessment

This hardening addresses an argument-level policy gap. It is not evidence of an unauthenticated remote execution path. The autonomous surface remains narrower than the direct authenticated `/v1/exec` administrative endpoint, and the service runs under the dedicated non-root identity.

One residual limitation is lexical rather than filesystem-resolved path containment: a symlink already present inside the workspace could point outside it. The current control-plane policy therefore does not claim full filesystem sandboxing. Full containment remains the responsibility of the future runtime cgroup/sandbox design and target-host rehearsal.

## Implemented hardening

Commit `b8b930403a013cfed42c13cb37d4b72b2a46d449` changes `_approval()` to use `_safe_python_auto()` and `_safe_relative_arg()`.

Commit `5ee4cfa3914d76eb49004964e3e2d1f25e947c77` adds regression coverage for:

- safe pytest invocation and relative test paths;
- absolute and `..` paths;
- pytest plugin/configuration selectors;
- pytest ini overrides;
- safe compileall paths;
- unsupported compileall flags.

## Execution state

The current ChatGPT execution surface can inspect and commit repository files through GitHub but cannot execute the repository locally. The existing CI evidence therefore remains the authoritative execution evidence until a fresh workflow run verifies the hardening.

This audit does not activate runtime cgroup enforcement and does not weaken the existing fail-closed target-host rehearsal gate.
