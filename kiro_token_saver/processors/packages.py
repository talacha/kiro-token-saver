import re

from . import Processor

NOISE = re.compile(r"^(npm (http|timing|notice)|Downloading|Collecting|Using cached|Requirement already|\s*\d+%|\s*[#=>\-]{4,}|Fetching|Resolving|Progress)", re.I)
KEEP = re.compile(r"(error|warn|ERR!|deprecat|vulnerabilit|added \d+|Successfully installed|up to date|removed|changed|Installed|found \d+)", re.I)


class PackageInstallProcessor(Processor):
    name = "package-install"
    commands = ("npm", "yarn", "pnpm", "pip", "pip3", "bun", "poetry", "uv", "brew", "apt", "apt-get")

    def matches(self, argv):
        return super().matches(argv) and any(a in ("install", "add", "i", "ci", "update", "upgrade") for a in argv[1:3])

    def process(self, text, cfg):
        kept = [ln.rstrip() for ln in text.splitlines() if ln.strip() and not NOISE.match(ln) and KEEP.search(ln)]
        return "\n".join(kept[-cfg.tail_lines:]) if kept else "(install completed, no notable output)"
