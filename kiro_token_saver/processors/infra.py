import re

from . import Processor, collapse_repeats, head_tail

TF_NOISE = re.compile(r"(Refreshing state|Reading\.\.\.|Read complete|Still (creating|modifying|destroying))")


class InfraProcessor(Processor):
    """terraform / kubectl / docker: drop refresh + progress chatter, trim tables."""

    name = "infra"
    commands = ("terraform", "tofu", "kubectl", "docker", "helm")

    def process(self, text, cfg):
        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip() and not TF_NOISE.search(ln)]
        # docker build layer noise
        lines = [ln for ln in lines if not re.match(r"^#\d+ (sha256:|DONE|CACHED)", ln)]
        return "\n".join(head_tail(collapse_repeats(lines), cfg.head_lines, cfg.tail_lines))
