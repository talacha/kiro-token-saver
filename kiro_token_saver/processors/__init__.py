"""Processor registry. Each processor is a class with `matches(argv)` and `process(text, cfg)`."""
import re
from abc import ABC, abstractmethod

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class Processor(ABC):
    name = "base"
    commands: tuple = ()  # matched against the first token (or first two for "git diff")

    def matches(self, argv):
        if not argv:
            return False
        head = argv[0].rsplit("/", 1)[-1]
        return head in self.commands

    @abstractmethod
    def process(self, text: str, cfg) -> str: ...


def collapse_repeats(lines):
    """Collapse consecutive identical lines into 'line  (xN)'."""
    out, prev, n = [], None, 0
    for ln in lines:
        if ln == prev:
            n += 1
            continue
        if prev is not None:
            out.append(prev if n == 1 else f"{prev}  (x{n})")
        prev, n = ln, 1
    if prev is not None:
        out.append(prev if n == 1 else f"{prev}  (x{n})")
    return out


def head_tail(lines, head, tail):
    if len(lines) <= head + tail:
        return lines
    omitted = len(lines) - head - tail
    return lines[:head] + [f"... [{omitted} lines omitted by token-saver] ..."] + lines[-tail:]


from .generic import GenericProcessor  # noqa: E402
from .git import GitProcessor  # noqa: E402
from .tests import TestProcessor  # noqa: E402
from .packages import PackageInstallProcessor  # noqa: E402
from .infra import InfraProcessor  # noqa: E402
from .lint import LintProcessor  # noqa: E402

PROCESSORS = [
    GitProcessor(),
    TestProcessor(),
    PackageInstallProcessor(),
    InfraProcessor(),
    LintProcessor(),
]
FALLBACK = GenericProcessor()


def select(argv):
    for p in PROCESSORS:
        if p.matches(argv):
            return p
    return FALLBACK
