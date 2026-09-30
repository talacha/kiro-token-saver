"""Config, compression pipeline, stats and delta mode."""
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from .processors import select, strip_ansi


@dataclass
class Config:
    enabled: bool = True
    min_chars: int = 400       # outputs shorter than this pass through untouched
    head_lines: int = 40
    tail_lines: int = 40
    diff_context: int = 1
    delta: bool = False        # experimental: collapse lines already seen in previous run
    state_dir: str = ""

    @classmethod
    def load(cls, env=None):
        env = os.environ if env is None else env
        cfg = cls()
        cfg.state_dir = env.get("TOKEN_SAVER_HOME", str(Path.home() / ".kiro" / "token-saver"))
        path = Path(env.get("TOKEN_SAVER_CONFIG", Path(cfg.state_dir) / "config.json"))
        if path.is_file():
            try:
                for k, v in json.loads(path.read_text()).items():
                    if hasattr(cfg, k) and k != "state_dir":
                        setattr(cfg, k, type(getattr(cfg, k))(v))
            except (ValueError, TypeError):
                pass  # bad config -> defaults
        if env.get("TOKEN_SAVER_DISABLED") == "1":
            cfg.enabled = False
        if env.get("TOKEN_SAVER_DELTA") == "1":
            cfg.delta = True
        return cfg


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4  # ~4 chars/token heuristic


def compress(text: str, argv, cfg: Config):
    """Return (compressed_text, processor_name). Never makes output longer."""
    if not cfg.enabled or len(text) < cfg.min_chars:
        return text, "passthrough"
    clean = strip_ansi(text)
    proc = select(argv)
    try:
        out = proc.process(clean, cfg)
    except Exception:  # a processor bug must never hide output
        return text, "passthrough"
    if cfg.delta:
        out = _delta(out, argv, cfg)
    if len(out) >= len(text):
        return text, "passthrough"
    return out, proc.name


def _delta(text, argv, cfg):
    """Replace lines identical to the previous run of the same command with a count."""
    d = Path(cfg.state_dir) / "delta"
    try:
        d.mkdir(parents=True, exist_ok=True)
        f = d / (hashlib.sha1(" ".join(argv).encode()).hexdigest() + ".json")
        prev = set(json.loads(f.read_text())) if f.is_file() else set()
        lines = text.splitlines()
        f.write_text(json.dumps(lines))
    except OSError:
        return text
    if not prev:
        return text
    new = [ln for ln in lines if ln not in prev]
    same = len(lines) - len(new)
    if not same:
        return text
    return "\n".join([f"[token-saver delta: {same} lines unchanged since last run]"] + new)


def record_stats(cfg, processor, before, after):
    try:
        Path(cfg.state_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(cfg.state_dir) / "stats.jsonl", "a") as fh:
            fh.write(json.dumps({"p": processor, "in": before, "out": after}) + "\n")
    except OSError:
        pass


def read_stats(cfg):
    path = Path(cfg.state_dir) / "stats.jsonl"
    total = {"runs": 0, "in": 0, "out": 0, "by_processor": {}}
    if not path.is_file():
        return total
    for ln in path.read_text().splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        total["runs"] += 1
        total["in"] += r["in"]
        total["out"] += r["out"]
        b = total["by_processor"].setdefault(r["p"], {"runs": 0, "in": 0, "out": 0})
        b["runs"] += 1
        b["in"] += r["in"]
        b["out"] += r["out"]
    return total
