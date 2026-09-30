import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kiro_token_saver.cli import main  # noqa: E402
from kiro_token_saver.core import Config, compress, read_stats  # noqa: E402
from kiro_token_saver.processors import select  # noqa: E402


def cfg(**kw):
    c = Config(state_dir=tempfile.mkdtemp())
    for k, v in kw.items():
        setattr(c, k, v)
    return c


class TestCompression(unittest.TestCase):
    def test_short_output_passthrough(self):
        out, name = compress("hello\n", ["ls"], cfg())
        self.assertEqual((out, name), ("hello\n", "passthrough"))

    def test_disabled(self):
        text = "x\n" * 1000
        self.assertEqual(compress(text, ["ls"], cfg(enabled=False))[0], text)

    def test_generic_collapses_repeats_and_ansi(self):
        text = "\x1b[31mwarn\x1b[0m\n" * 500
        out, name = compress(text, ["foo"], cfg())
        self.assertEqual(name, "generic")
        self.assertIn("warn  (x500)", out)
        self.assertNotIn("\x1b", out)

    def test_never_longer(self):
        text = "".join(f"line {i}\n" for i in range(30))
        out, _ = compress(text, ["foo"], cfg(min_chars=1))
        self.assertLessEqual(len(out), len(text))

    def test_git_diff_trims_context(self):
        ctx = "".join(f" context {i}\n" for i in range(200))
        diff = f"diff --git a/f b/f\nindex 1..2 100644\n--- a/f\n+++ b/f\n@@ -1,400 +1,400 @@\n{ctx}-old\n+new\n{ctx}"
        out, name = compress(diff, ["git", "diff"], cfg())
        self.assertEqual(name, "git")
        self.assertIn("-old", out)
        self.assertIn("+new", out)
        self.assertIn("context lines omitted", out)
        self.assertNotIn("index 1..2", out)
        self.assertLess(len(out), len(diff) / 5)

    def test_pytest_keeps_failure_and_summary(self):
        passing = "".join(f"tests/test_a.py::test_{i} PASSED\n" for i in range(300))
        text = (passing + "=== FAILURES ===\n___ test_bad ___\nE   assert 1 == 2\n"
                "=== 1 failed, 300 passed in 2s ===\n")
        out, name = compress(text, ["pytest"], cfg())
        self.assertEqual(name, "tests")
        self.assertIn("assert 1 == 2", out)
        self.assertIn("1 failed, 300 passed", out)
        self.assertNotIn("test_150 PASSED", out)

    def test_npm_install_reduced(self):
        text = "".join(f"npm http fetch GET 200 pkg{i}\n" for i in range(100)) + "added 120 packages in 3s\n"
        out, name = compress(text, ["npm", "install"], cfg())
        self.assertEqual(name, "package-install")
        self.assertEqual(out.strip(), "added 120 packages in 3s")

    def test_terraform_drops_refresh(self):
        text = "".join(f"aws_x.r{i}: Refreshing state... [id=i{i}]\n" for i in range(50)) + "Plan: 1 to add, 0 to change.\n"
        out, _ = compress(text, ["terraform", "plan"], cfg())
        self.assertIn("Plan: 1 to add", out)
        self.assertNotIn("Refreshing", out)

    def test_lint_rule_counts(self):
        text = "".join(f"a.py:{i}:1: E501 line too long\n" for i in range(60))
        out, name = compress(text, ["ruff", "check"], cfg())
        self.assertEqual(name, "lint")
        self.assertIn("E501=+57", out)
        self.assertEqual(out.count("line too long"), 3)

    def test_selection(self):
        self.assertEqual(select(["git", "status"]).name, "git")
        self.assertEqual(select(["go", "test", "./..."]).name, "tests")
        self.assertEqual(select(["whatever"]).name, "generic")

    def test_deterministic(self):
        text = "a\n" * 600
        c = cfg()
        self.assertEqual(compress(text, ["x"], c), compress(text, ["x"], c))

    def test_delta_mode(self):
        c = cfg(delta=True, min_chars=1)
        text = "".join(f"error in file{i}\n" for i in range(40))
        first, _ = compress(text, ["make"], c)
        second, _ = compress(text + "error new\n", ["make"], c)
        self.assertIn("unchanged since last run", second)
        self.assertIn("error new", second)
        self.assertNotIn("error in file3", second)
        self.assertNotIn("unchanged", first)


class TestCli(unittest.TestCase):
    def run_cli(self, argv, c):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(argv, c)
        return rc, buf.getvalue()

    def test_run_preserves_exit_code_and_records_stats(self):
        c = cfg()
        rc, out = self.run_cli(["run", "--", sys.executable, "-c",
                                "print('x\\n'*2000); import sys; sys.exit(3)"], c)
        self.assertEqual(rc, 3)
        self.assertLess(len(out), 500)
        self.assertEqual(read_stats(c)["runs"], 1)

    def test_stats_output(self):
        c = cfg()
        self.run_cli(["run", "--", sys.executable, "-c", "print('y\\n'*2000)"], c)
        rc, out = self.run_cli(["stats"], c)
        self.assertEqual(rc, 0)
        self.assertIn("saved", out)

    def test_config_file_and_env(self):
        d = tempfile.mkdtemp()
        (Path(d) / "config.json").write_text(json.dumps({"min_chars": 7, "head_lines": 5}))
        c = Config.load({"TOKEN_SAVER_HOME": d, "TOKEN_SAVER_DELTA": "1"})
        self.assertEqual((c.min_chars, c.head_lines, c.delta), (7, 5, True))
        self.assertFalse(Config.load({"TOKEN_SAVER_HOME": d, "TOKEN_SAVER_DISABLED": "1"}).enabled)

    def test_missing_command(self):
        rc, _ = self.run_cli(["run", "--", "definitely-not-a-command-xyz"], cfg())
        self.assertEqual(rc, 127)


if __name__ == "__main__":
    unittest.main()
