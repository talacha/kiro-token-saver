# kiro-token-saver

A Kiro port of [token-saver](https://ppgranger.github.io/token-saver/): compress verbose terminal output
(`git diff`, `pytest`, `npm install`, `terraform plan`, linters) **locally and deterministically** before the
agent reads it. No LLM calls, no network. Same input and config give the same output.

## How it differs from the original

The original is a Claude Code plugin that intercepts tool output via hooks. Kiro has no hook that rewrites
shell output, so this port uses an explicit wrapper instead: a Kiro **Power** whose steering file tells the agent
to run noisy commands as `python -m kiro_token_saver run -- <cmd>`. It compresses only when the agent follows
that steering. This is a reimplementation from the public description, not a copy of the original's code, and
it covers 5 processor families plus a generic fallback, not the original's 36.

## Install

```
pip install -e .          # optional; provides the `token-saver` command
```

Kiro: add `power/` as a local Power (Powers panel, Add power from local path). For a single workspace, copy
`power/steering/token-saver.md` to `.kiro/steering/`.

## Usage

```
python -m kiro_token_saver run -- pytest -q        # run + compress, exit code preserved
git diff | python -m kiro_token_saver filter --cmd "git diff"
python -m kiro_token_saver stats
```

## Processors

| Processor | Matches | Strategy |
|---|---|---|
| git | `git ...` | diff: keep changed lines + `diff_context` lines, drop `index` lines; else head/tail |
| tests | pytest, jest, vitest, mocha, rspec, `go test`, `cargo test`, `npm test` | keep failures and summary lines |
| package-install | npm/yarn/pnpm/pip/uv/brew/apt install | drop progress; keep errors, warnings, totals |
| infra | terraform, tofu, kubectl, docker, helm | drop refresh/progress/layer noise, collapse repeats |
| lint | eslint, ruff, flake8, mypy, tsc, ... | first 3 diagnostics per rule, counts for the rest |
| generic | everything else | strip ANSI, squeeze blanks, collapse repeats, head/tail |

Safety: output under `min_chars` passes through; compressed output is never longer than the original; a processor
exception falls back to raw output.

## Configuration

`~/.kiro/token-saver/config.json` (dir override: `TOKEN_SAVER_HOME`, file override: `TOKEN_SAVER_CONFIG`):

| Key | Default | Meaning |
|---|---|---|
| enabled | true | master switch |
| min_chars | 400 | skip compression below this size |
| head_lines / tail_lines | 40 / 40 | kept when truncating |
| diff_context | 1 | context lines around diff changes |
| delta | false | experimental: collapse lines unchanged since the previous run of the same command |

Env: `TOKEN_SAVER_DISABLED=1`, `TOKEN_SAVER_DELTA=1`. Token counts in `stats` are a ~4 chars/token estimate.

## Tests

```
python3 -m unittest discover -s tests -v
```
