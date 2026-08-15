import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/finish-worktree/scripts/consolidate_task_commit.py"


def git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class FinishWorktreeConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.base = root / "base"
        self.task = root / "task"
        self.marker = root / "pre-commit-ran"
        self.message = root / "message.txt"

        git(root, "init", "--quiet", "--initial-branch=main", str(self.base))
        git(self.base, "config", "user.name", "SmartKit Test")
        git(self.base, "config", "user.email", "smartkit@example.invalid")
        (self.base / "artifact.txt").write_text("base\n", encoding="utf-8")
        git(self.base, "add", "artifact.txt")
        git(self.base, "commit", "--quiet", "-m", "base")
        self.target = git(self.base, "rev-parse", "HEAD")
        git(self.base, "worktree", "add", "--quiet", "-b", "task", str(self.task))

        (self.task / "artifact.txt").write_text("checkpoint one\n", encoding="utf-8")
        git(self.task, "commit", "--quiet", "-am", "checkpoint one")
        (self.task / "artifact.txt").write_text("checkpoint two\n", encoding="utf-8")
        git(self.task, "commit", "--quiet", "-am", "review fix")
        self.checkpoint_head = git(self.task, "rev-parse", "HEAD")
        self.checkpoint_tree = git(self.task, "rev-parse", "HEAD^{tree}")
        self.message.write_text("feat: deliver task\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def install_hook(self, exit_code: int) -> None:
        hooks = Path(git(self.task, "rev-parse", "--git-common-dir")) / "hooks"
        if not hooks.is_absolute():
            hooks = (self.task / hooks).resolve()
        hook = hooks / "pre-commit"
        hook.write_text(
            f"#!/bin/sh\nprintf ran > '{self.marker}'\nexit {exit_code}\n",
            encoding="utf-8",
        )
        hook.chmod(hook.stat().st_mode | 0o111)

    def run_script(
        self, recovery_ref: str, target: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repository",
                str(self.task),
                "--target",
                target or self.target,
                "--message-file",
                str(self.message),
                "--recovery-ref",
                recovery_ref,
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )

    def test_consolidates_checkpoints_through_normal_commit_hooks(self):
        self.install_hook(0)
        recovery_ref = "refs/smartkit/recovery/task/success"

        result = self.run_script(recovery_ref)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        task_commit = payload["task_commit"]
        self.assertTrue(self.marker.exists())
        self.assertEqual(git(self.task, "symbolic-ref", "--short", "HEAD"), "task")
        self.assertEqual(git(self.task, "rev-list", "--count", "main..task"), "1")
        self.assertEqual(git(self.task, "show", "-s", "--format=%P", task_commit), self.target)
        self.assertEqual(git(self.task, "rev-parse", f"{task_commit}^{{tree}}"), self.checkpoint_tree)
        self.assertEqual(git(self.task, "rev-parse", recovery_ref), self.checkpoint_head)
        self.assertEqual(git(self.task, "status", "--porcelain"), "")

    def test_rejected_hook_restores_task_branch_and_retains_recovery(self):
        self.install_hook(1)
        recovery_ref = "refs/smartkit/recovery/task/rejected"

        result = self.run_script(recovery_ref)

        self.assertEqual(result.returncode, 1)
        self.assertTrue(self.marker.exists())
        self.assertEqual(git(self.task, "symbolic-ref", "--short", "HEAD"), "task")
        self.assertEqual(git(self.task, "rev-parse", "HEAD"), self.checkpoint_head)
        self.assertEqual(git(self.task, "rev-parse", recovery_ref), self.checkpoint_head)
        self.assertEqual(git(self.task, "status", "--porcelain"), "")

    def test_existing_recovery_ref_is_rejected_without_mutating_task(self):
        recovery_ref = "refs/smartkit/recovery/task/existing"
        git(self.task, "update-ref", recovery_ref, self.checkpoint_head)

        result = self.run_script(recovery_ref)

        self.assertEqual(result.returncode, 1)
        self.assertIn("recovery ref already exists", result.stderr)
        self.assertEqual(git(self.task, "symbolic-ref", "--short", "HEAD"), "task")
        self.assertEqual(git(self.task, "rev-parse", "HEAD"), self.checkpoint_head)
        self.assertEqual(git(self.task, "rev-parse", recovery_ref), self.checkpoint_head)
        self.assertEqual(git(self.task, "status", "--porcelain"), "")

    def test_equal_target_is_rejected_without_creating_empty_commit(self):
        recovery_ref = "refs/smartkit/recovery/task/already-delivered"

        result = self.run_script(recovery_ref, target=self.checkpoint_head)

        self.assertEqual(result.returncode, 1)
        self.assertIn("checkpoint HEAD equals the delivery target", result.stderr)
        self.assertEqual(git(self.task, "symbolic-ref", "--short", "HEAD"), "task")
        self.assertEqual(git(self.task, "rev-parse", "HEAD"), self.checkpoint_head)
        self.assertNotEqual(
            subprocess.run(
                ["git", "-C", str(self.task), "show-ref", "--verify", "--quiet", recovery_ref],
                check=False,
            ).returncode,
            0,
        )
        self.assertEqual(git(self.task, "status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
