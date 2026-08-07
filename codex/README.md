# Codex adapter

This directory keeps Codex-specific installation and agent recipes out of the model-independent SOP layer.

## Two AGENTS scopes

- `AGENTS.global.md` is a personal, cross-repository Supervisor template. Install it as `~/.codex/AGENTS.md` when those defaults should apply to every new Codex run.
- The repository-root `../AGENTS.md` explains how to maintain this repository. Project files load after global guidance and provide more specific rules for their directory tree.

Do not copy the global template into every project. Keep project commands, architecture, and verification requirements in that project's `AGENTS.md`; keep reusable personal working agreements in the global file. Never put API keys, tokens, provider credentials, billing data, or private authentication material in either file.

## Backup and install

From the repository root:

```sh
mkdir -p ~/.codex
if test -s ~/.codex/AGENTS.md; then
  cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.backup-$(date +%Y%m%d-%H%M%S)
fi
cp codex/AGENTS.global.md ~/.codex/AGENTS.md
cmp codex/AGENTS.global.md ~/.codex/AGENTS.md
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

Remove the installed file only when you intend to remove global guidance, then start a new Session:

```sh
rm ~/.codex/AGENTS.md
```

To restore a backup, copy the selected timestamped file back to `~/.codex/AGENTS.md`, verify it with `cmp`, and start a new Session. Backups are local runtime files and must not be committed here.

## Agent templates

`agents/` contains project-portable custom-agent templates using the current Codex custom-agent schema. Copy selected files to `.codex/agents/` in a trusted project or to `~/.codex/agents/` for personal use.

The adapter maps semantic roles to models as follows:

| Role | Model | Effort | Sandbox |
|---|---|---|---|
| explorer | `gpt-5.6-luna` | medium | read-only |
| focused_worker | `gpt-5.6-luna` | high | workspace-write |
| worker | `gpt-5.6-terra` | high | workspace-write |
| verifier | `gpt-5.6-luna` | medium | workspace-write, no source edits |
| reviewer | `gpt-5.6-terra` | high | read-only |
| risk_reviewer | `gpt-5.6` | high | read-only |

Official Codex documentation currently verifies `gpt-5.6`, `gpt-5.6-terra`, and `gpt-5.6-luna`. It does not establish `gpt-5.6-sol` as a model slug, so the high-risk/Sol semantic role uses the documented demanding-agent model `gpt-5.6` rather than an inferred name. Prices are intentionally absent; routing is based on role capability and relative cost, not volatile numbers.

These files do not change the user's provider, authentication, or global model defaults. A custom agent's explicit model and reasoning effort apply only when that agent is selected.

## Official references

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and custom agent files](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
