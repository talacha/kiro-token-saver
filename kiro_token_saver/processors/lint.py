import re
from collections import Counter

from . import Processor, head_tail

RULE = re.compile(r"\b([A-Z]{1,4}\d{2,4}|[a-z]+(?:[-/][a-z0-9]+)+)\b\s*$|\b([A-Z]{1,4}\d{2,4})\b")
PER_RULE = 3  # diagnostics kept verbatim per rule


class LintProcessor(Processor):
    """eslint/ruff/flake8/mypy/tsc: keep first few diagnostics per rule, count the rest."""

    name = "lint"
    commands = ("eslint", "ruff", "flake8", "pylint", "mypy", "tsc", "golangci-lint", "rubocop", "clippy")

    def process(self, text, cfg):
        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
        seen, totals, out = Counter(), Counter(), []
        for ln in lines:
            m = RULE.search(ln)
            rule = (m.group(1) or m.group(2)) if m else None
            if rule is None:
                out.append(ln)
                continue
            totals[rule] += 1
            seen[rule] += 1
            if seen[rule] <= PER_RULE:
                out.append(ln)
        out = head_tail(out, cfg.head_lines, cfg.tail_lines)
        extra = {r: n - PER_RULE for r, n in totals.items() if n > PER_RULE}
        if extra:
            top = ", ".join(f"{r}=+{n}" for r, n in sorted(extra.items(), key=lambda kv: -kv[1])[:8])
            out.append(f"[token-saver] additional diagnostics not shown: {top}")
        return "\n".join(out)
