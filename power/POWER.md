---
name: "token-saver"
displayName: "Token Saver"
description: "Compress verbose terminal output (git diff, pytest, npm install, terraform, lint) before the agent reads it, locally and deterministically."
keywords: ["tokens", "compression", "terminal", "git diff", "pytest", "npm install", "terraform", "context"]
author: "kiro-token-saver"
---

# Token Saver

Wraps shell commands with `token-saver run --`, which executes the command, then compresses
its output with a processor specific to that command family. No LLM calls, no network.

## Usage

Prefix noisy commands:

```
python -m kiro_token_saver run -- git diff
python -m kiro_token_saver run -- pytest -q
python -m kiro_token_saver run -- npm install
```

The wrapped command's exit code is preserved. Output shorter than `min_chars` is untouched,
and compressed output is never longer than the original.

See `steering/token-saver.md` for the rules Kiro follows when deciding to wrap a command.

## Commands

- `run -- <cmd>`: execute and compress
- `filter --cmd "<cmd>"`: compress stdin
- `stats`: savings so far

## Configuration

`~/.kiro/token-saver/config.json` (override dir with `TOKEN_SAVER_HOME`):
`enabled`, `min_chars`, `head_lines`, `tail_lines`, `diff_context`, `delta`.
Env: `TOKEN_SAVER_DISABLED=1`, `TOKEN_SAVER_DELTA=1`.

## Troubleshooting

If compressed output hides something you need, rerun the command without the wrapper
or with `TOKEN_SAVER_DISABLED=1`.
