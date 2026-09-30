from . import Processor, collapse_repeats, head_tail


class GitProcessor(Processor):
    """git diff: reduce context lines around hunks. git log/status: trim."""

    name = "git"
    commands = ("git",)

    def process(self, text, cfg):
        lines = text.splitlines()
        if any(ln.startswith("diff --git") for ln in lines):
            return "\n".join(self._diff(lines, cfg.diff_context))
        return "\n".join(head_tail(collapse_repeats([ln.rstrip() for ln in lines]), cfg.head_lines, cfg.tail_lines))

    @staticmethod
    def _diff(lines, ctx):
        keep = [False] * len(lines)
        changed = [i for i, ln in enumerate(lines)
                   if (ln.startswith(("+", "-")) and not ln.startswith(("+++", "---")))]
        for i, ln in enumerate(lines):
            if ln.startswith(("diff --git", "@@", "+++", "---", "new file", "deleted file", "rename ", "Binary")):
                keep[i] = True
        for i in changed:
            for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
                keep[j] = True
        out, skipped = [], 0
        for i, ln in enumerate(lines):
            if keep[i]:
                if skipped:
                    out.append(f" ... [{skipped} context lines omitted]")
                    skipped = 0
                if ln.startswith("index "):
                    continue
                out.append(ln)
            else:
                skipped += 1
        if skipped:
            out.append(f" ... [{skipped} context lines omitted]")
        return [ln for ln in out if not ln.startswith("index ")]
