# Workspace adapter

## Authority

- The directory containing this installed file is the workspace boundary unless a closer project `AGENTS.md` declares a narrower root.
- `~/.codex/runtime-current` is immutable installed output. Change the source `agent-sop` repository and reinstall instead of editing installed files.
- Reusable execution semantics come from the runtime Kernel; Codex routing comes from `codex/CODEX-ADAPTER.md`. This workspace file supplies local discovery only.

## Local resources

- Discover projects, notes, datasets, models, and run directories from the closest project instructions and the actual local filesystem. Do not infer an absent directory from memory and do not create a historical layout unless the task requires it.
- Discover remote compute from the project contract, `~/.ssh/config` including its `Include` files, and an explicitly configured local resource inventory if one exists. Reusable instructions must not contain a default host, IP, username, private path, card number, or credential.
- Before freezing a remote work packet, use read-only probes to confirm host identity, available accelerator/VRAM, load, disk, authorized workspace, and current availability. An authorized host alias/resource envelope can be used autonomously; new credentials, shared-resource conflicts, unbounded spend, destructive cleanup, and production/public actions remain HUMAN boundaries.
- Evidence-bearing remote runs remain fail-fast and keep immutable raw artifacts, logs, command, process/job identity, host/device, repo/environment identity, cost, status, and output location. Do not silently substitute local CPU, another host, backend, model, dataset, metric, or method.

## Local safety

- Preserve user changes, secrets, and recoverable data. Write only inside the resolved project/workspace root.
- Follow the closest project commands and verification contract; do not impose a global package manager, directory tree, server, or deployment platform.
