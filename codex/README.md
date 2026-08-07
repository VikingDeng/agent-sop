# Codex adapter

This directory keeps Codex-specific installation and agent recipes out of the model-independent SOP layer.

## Two AGENTS scopes

- `AGENTS.global.md` is the personal, cross-repository Supervisor source. Link it as `~/.codex/AGENTS.md` when those defaults should apply to every new Codex run.
- `AGENTS.workspace.md` is the lightweight `/Users/viking` workspace overlay. Link it as `/Users/viking/AGENTS.md`; project-local `AGENTS.md` files may narrow it further.
- The repository-root `../AGENTS.md` explains how to maintain this repository. Project files load after global guidance and provide more specific rules for their directory tree.

Do not copy the global template into every project. Keep project commands, architecture, and verification requirements in that project's `AGENTS.md`; keep reusable personal working agreements in the global file. Never put API keys, tokens, provider credentials, billing data, or private authentication material in either file.

## Backup and install

The managed installation keeps this repository authoritative:

```sh
set -eu
agent_sop_root="$PWD"
agent_sop_stamp="$(date +%Y%m%d-%H%M%S)-$$"
agent_sop_roles="explorer focused_worker worker verifier reviewer risk_reviewer"
test -f "$agent_sop_root/codex/AGENTS.global.md"
test -f "$agent_sop_root/codex/AGENTS.workspace.md"
for agent_role in $agent_sop_roles; do
  test -f "$agent_sop_root/codex/agents/$agent_role.toml"
done
test -f "$agent_sop_root/codex/skills/research-execution-grill/SKILL.md"

for runtime_path in \
  "$HOME/.codex/AGENTS.md" \
  "/Users/viking/AGENTS.md" \
  "$HOME/.codex/skills/research-execution-grill"
do
  if test -d "$runtime_path" && ! test -L "$runtime_path"; then
    echo "refusing to replace real directory: $runtime_path" >&2
    exit 1
  fi
done
for agent_role in $agent_sop_roles; do
  runtime_path="$HOME/.codex/agents/$agent_role.toml"
  if test -d "$runtime_path" && ! test -L "$runtime_path"; then
    echo "refusing to replace real directory: $runtime_path" >&2
    exit 1
  fi
done

mkdir -p "$HOME/.codex/agents" "$HOME/.codex/skills"
if test -e "$HOME/.codex/AGENTS.md" || test -L "$HOME/.codex/AGENTS.md"; then
  backup_path="$HOME/.codex/AGENTS.md.backup-$agent_sop_stamp"
  cp -R -L "$HOME/.codex/AGENTS.md" "$backup_path"
  cmp "$HOME/.codex/AGENTS.md" "$backup_path"
fi
if test -e /Users/viking/AGENTS.md || test -L /Users/viking/AGENTS.md; then
  backup_path="/Users/viking/AGENTS.md.backup-$agent_sop_stamp"
  cp -R -L /Users/viking/AGENTS.md "$backup_path"
  cmp /Users/viking/AGENTS.md "$backup_path"
fi
for agent_role in $agent_sop_roles; do
  runtime_path="$HOME/.codex/agents/$agent_role.toml"
  if test -e "$runtime_path" || test -L "$runtime_path"; then
    backup_path="$runtime_path.backup-$agent_sop_stamp"
    cp -R -L "$runtime_path" "$backup_path"
    cmp "$runtime_path" "$backup_path"
  fi
done
runtime_skill="$HOME/.codex/skills/research-execution-grill"
if test -e "$runtime_skill" || test -L "$runtime_skill"; then
  backup_path="$runtime_skill.backup-$agent_sop_stamp"
  cp -R -L "$runtime_skill" "$backup_path"
  diff -qr "$runtime_skill" "$backup_path"
fi

ln -sfn "$agent_sop_root/codex/AGENTS.global.md" "$HOME/.codex/AGENTS.md"
ln -sfn "$agent_sop_root/codex/AGENTS.workspace.md" /Users/viking/AGENTS.md
for agent_role in $agent_sop_roles; do
  ln -sfn "$agent_sop_root/codex/agents/$agent_role.toml" "$HOME/.codex/agents/$agent_role.toml"
done
ln -sfn "$agent_sop_root/codex/skills/research-execution-grill" "$runtime_skill"

test "$(readlink "$HOME/.codex/AGENTS.md")" = "$agent_sop_root/codex/AGENTS.global.md"
test "$(readlink /Users/viking/AGENTS.md)" = "$agent_sop_root/codex/AGENTS.workspace.md"
for agent_role in $agent_sop_roles; do
  test "$(readlink "$HOME/.codex/agents/$agent_role.toml")" = "$agent_sop_root/codex/agents/$agent_role.toml"
done
test "$(readlink "$runtime_skill")" = "$agent_sop_root/codex/skills/research-execution-grill"
```

An empty destination needs no semantic merge. A non-empty destination must be backed up and reviewed before replacement; do not silently discard personal rules.

Codex discovers AGENTS guidance once when a run starts. Start a new Session after installing, changing, or removing the global file. A current Session does not retroactively reload it.

To ask a new run which instruction sources it loaded:

```sh
codex --ask-for-approval never "List the instruction sources you loaded."
codex --cd <project> --ask-for-approval never "List the instruction sources you loaded."
```

The first command checks global guidance; the second also checks the project chain. Codex skips empty AGENTS files and loads at most one applicable instruction file per directory.

## Uninstall or restore

Remove only the managed symlinks when you intend to uninstall the adapter, then start a new Session:

```sh
rm "$HOME/.codex/AGENTS.md" /Users/viking/AGENTS.md
for agent_role in explorer focused_worker worker verifier reviewer risk_reviewer; do
  rm "$HOME/.codex/agents/$agent_role.toml"
done
rm "$HOME/.codex/skills/research-execution-grill"
```

To restore a backup, copy the selected timestamped file back to its original AGENTS, agent-role, or skill path, verify it with `cmp` (or a recursive diff for a directory), and start a new Session. Backups are local runtime files and must not be committed here.

## Agent templates

`agents/` contains project-portable custom-agent templates using the current Codex custom-agent schema. The managed personal installation links the six role files into `~/.codex/agents/`; project-local files may override them for a trusted repository.

The adapter maps semantic roles to models as follows:

| Role | Model | Effort | Sandbox |
|---|---|---|---|
| explorer | `gpt-5.6-luna` | medium | read-only |
| focused_worker | `gpt-5.6-luna` | high | workspace-write |
| worker | `gpt-5.6-terra` | high | workspace-write |
| verifier | `gpt-5.6-luna` | medium | workspace-write, no source edits |
| reviewer | `gpt-5.6-terra` | high | read-only |
| risk_reviewer | `gpt-5.6-sol` | max | read-only |

The current Codex host exposes `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna`. The foreground Supervisor defaults to Sol Max; delegated roles reserve Sol Max for high-risk independent review, use Terra for ordinary implementation/review, and use Luna for bounded or mechanical work. Prices are intentionally absent; routing is based on role capability and relative cost, not volatile numbers.

These files do not change the user's provider, authentication, or global model defaults. A custom agent's explicit model and reasoning effort apply only when that agent is selected.

The personal runtime also sets `[agents].max_concurrent_threads_per_session = 2` and `max_depth = 1`. This makes the Supervisor's two-agent policy a runtime cap and prevents recursive agent trees; it does not require two agents when direct work is sufficient.

`skills/research-execution-grill/` is a thin Codex adapter for the authoritative SOP at `../sop/tier1-skeleton/research-execution-grill.md`. Link it into `~/.codex/skills/research-execution-grill` so the repository remains the editable source of truth. Restart Codex after changing AGENTS files, custom agents, or installed skills.

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
