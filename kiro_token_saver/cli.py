"""CLI:  token-saver run -- <cmd...> | token-saver filter [--cmd "git diff"] | token-saver stats"""
import argparse
import shlex
import subprocess
import sys

from .core import Config, compress, estimate_tokens, read_stats, record_stats


def _emit(text, argv, cfg, rc=0):
    out, name = compress(text, argv, cfg)
    record_stats(cfg, name, estimate_tokens(text), estimate_tokens(out))
    sys.stdout.write(out if out.endswith("\n") or not out else out + "\n")
    return rc


def cmd_run(args, cfg):
    argv = [a for a in args.command if a != "--"]
    if not argv:
        print("usage: token-saver run -- <command...>", file=sys.stderr)
        return 2
    try:
        p = subprocess.run(argv, capture_output=True, text=True, errors="replace")
    except FileNotFoundError:
        print(f"token-saver: command not found: {argv[0]}", file=sys.stderr)
        return 127
    return _emit(p.stdout + p.stderr, argv, cfg, p.returncode)


def cmd_filter(args, cfg):
    return _emit(sys.stdin.read(), shlex.split(args.cmd), cfg)


def cmd_stats(args, cfg):
    s = read_stats(cfg)
    if not s["runs"]:
        print("No token-saver runs recorded yet.")
        return 0
    saved = s["in"] - s["out"]
    pct = 100 * saved / s["in"] if s["in"] else 0
    print(f"Runs: {s['runs']}  Tokens in: {s['in']}  out: {s['out']}  saved: {saved} ({pct:.1f}%)")
    for name, b in sorted(s["by_processor"].items()):
        sv = b["in"] - b["out"]
        print(f"  {name:<16} runs={b['runs']:<4} saved={sv} ({100 * sv / b['in'] if b['in'] else 0:.1f}%)")
    return 0


def main(argv=None, cfg=None):
    ap = argparse.ArgumentParser(prog="token-saver")
    sub = ap.add_subparsers(dest="sub", required=True)
    r = sub.add_parser("run", help="run a command and compress its output")
    r.add_argument("command", nargs=argparse.REMAINDER)
    r.set_defaults(fn=cmd_run)
    f = sub.add_parser("filter", help="compress stdin")
    f.add_argument("--cmd", default="", help="command that produced the input, for processor selection")
    f.set_defaults(fn=cmd_filter)
    s = sub.add_parser("stats", help="show savings")
    s.set_defaults(fn=cmd_stats)
    args = ap.parse_args(argv)
    return args.fn(args, cfg or Config.load())


if __name__ == "__main__":
    sys.exit(main())
