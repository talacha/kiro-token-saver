---
inclusion: always
---

# Token Saver steering

When running shell commands that usually produce long output, run them through the wrapper:

`python -m kiro_token_saver run -- <command>`

Wrap: `git diff`, `git log`, test runners (pytest, jest, go test, cargo test, npm test),
package installs, `terraform plan/apply`, `kubectl`, `docker build`, linters and type checkers.

Do not wrap: interactive commands, commands whose exact raw output matters (e.g. `cat` of a file
you will edit, `git diff` you will apply as a patch), or short commands.

If the compressed output omits something you need, rerun with `TOKEN_SAVER_DISABLED=1`.
