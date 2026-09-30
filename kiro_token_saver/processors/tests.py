import re

from . import Processor, head_tail

FAIL_HINT = re.compile(r"(FAIL|ERROR|Error|Traceback|assert|✕|✗|panicked|Exception)")
SUMMARY = re.compile(r"(\d+ (passed|failed|skipped|error)|Tests:|Test Suites:|test result:|=+ .* =+$|^ok\b|^FAIL\b)")


class TestProcessor(Processor):
    """pytest/jest/go test/cargo test: drop passing noise, keep failures + summary."""

    __test__ = False  # not a pytest class
    name = "tests"
    commands = ("pytest", "py.test", "jest", "vitest", "mocha", "rspec", "phpunit")

    def matches(self, argv):
        if super().matches(argv):
            return True
        joined = " ".join(argv[:3])
        return any(k in joined for k in ("pytest", "go test", "cargo test", "npm test", "npm run test", "yarn test", "pnpm test"))

    def process(self, text, cfg):
        lines = [ln.rstrip() for ln in text.splitlines()]
        out, in_fail = [], False
        for ln in lines:
            if re.match(r"^_{3,} .* _{3,}$|^={3,} (FAILURES|ERRORS) ={3,}$|^--- FAIL|^● ", ln):
                in_fail = True
            if in_fail or FAIL_HINT.search(ln) or SUMMARY.search(ln):
                out.append(ln)
            elif re.match(r"^={3,} .* ={3,}$", ln):
                in_fail = False
        if not out:  # nothing recognisable -> keep the tail, where summaries live
            out = lines[-cfg.tail_lines:]
        return "\n".join(head_tail(out, cfg.head_lines, cfg.tail_lines))
