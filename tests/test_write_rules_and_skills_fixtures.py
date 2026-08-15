import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "write-rules-and-skills"

EXPECTED_CASES = {
    "shared-rule": ("ordinary-artifact", "rule", "shared"),
    "project-local-rule": ("ordinary-artifact", "rule", "project-local"),
    "rule-generation-contract": ("generation-contract", "rule", "cross-project"),
    "shared-skill": ("ordinary-artifact", "skill", "shared"),
    "project-local-skill": ("ordinary-artifact", "skill", "project-local"),
    "skill-generation-contract": ("generation-contract", "skill", "cross-project"),
}


def load_case(case_id):
    return json.loads((FIXTURE_ROOT / case_id / "case.json").read_text(encoding="utf-8"))


def run_entry(root, argv):
    return subprocess.run(
        argv,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


class WriteRulesAndSkillsFixtureTest(unittest.TestCase):
    def test_fixture_inventory_and_structured_contract(self):
        self.assertEqual(
            {path.name for path in FIXTURE_ROOT.iterdir() if path.is_dir()},
            set(EXPECTED_CASES),
        )

        forbidden_parts = {
            ".git",
            "candidate",
            "qualification",
            "report",
            "sandbox",
            "verdict",
        }
        for path in FIXTURE_ROOT.rglob("*"):
            if path.is_file():
                self.assertTrue(forbidden_parts.isdisjoint(path.relative_to(FIXTURE_ROOT).parts))

        for case_id, expected_class in EXPECTED_CASES.items():
            with self.subTest(case=case_id):
                case_root = FIXTURE_ROOT / case_id
                case = load_case(case_id)
                self.assertNotIn("version", case)
                self.assertEqual(case["id"], case_id)
                self.assertEqual(
                    (case["lifecycle"], case["semantic_type"], case["scope"]),
                    expected_class,
                )
                expected_mode = (
                    "isolated-runner"
                    if case["lifecycle"] == "ordinary-artifact"
                    else "static-walkthrough"
                )
                self.assertEqual(case["acceptance_mode"], expected_mode)
                self.assertTrue((case_root / case["request"]).is_file())
                self.assertEqual(case["initial_state"]["candidate"], "absent")
                candidate_contract = case["candidate_contract"]
                self.assertIn(candidate_contract["format"], {"markdown", "skill-package"})
                self.assertFalse(Path(candidate_contract["relative_path"]).is_absolute())
                if candidate_contract["format"] == "skill-package":
                    self.assertRegex(candidate_contract["name"], r"^[a-z0-9-]+$")

                acceptance_cases = case["acceptance_cases"]
                self.assertGreaterEqual(len(acceptance_cases), 2)
                self.assertLessEqual(len(acceptance_cases), 4)
                self.assertEqual(
                    len({item["id"] for item in acceptance_cases}),
                    len(acceptance_cases),
                )
                for item in acceptance_cases:
                    self.assertEqual(set(item), {"id", "risk", "input", "expected"})

                evidence_paths = list(case.get("evidence", []))
                if case["scope"] == "shared":
                    representative = case["representative_context"]
                    portability = case["portability_evidence"]
                    self.assertTrue(portability)
                    evidence_items = [representative, *portability]
                    second_context = case.get("second_context")
                    if second_context is not None:
                        self.assertTrue(second_context["reason"].strip())
                        self.assertNotEqual(second_context["id"], representative["id"])
                        evidence_items.append(second_context)
                    evidence_ids = [item["id"] for item in evidence_items]
                    self.assertEqual(len(evidence_ids), len(set(evidence_ids)))
                    evidence_paths.extend(item["path"] for item in evidence_items)
                self.assertTrue(evidence_paths)
                for relative_path in evidence_paths:
                    evidence_path = (case_root / relative_path).resolve()
                    self.assertTrue(evidence_path.is_relative_to(case_root.resolve()))
                    self.assertTrue(evidence_path.is_file())

                if case["scope"] == "project-local":
                    project_root = case_root / case["project_root"]
                    self.assertTrue(project_root.is_dir())
                    self.assertTrue((project_root / "AGENTS.md").is_file())
                if case["lifecycle"] == "generation-contract":
                    self.assertNotIn("project_root", case)
                    self.assertEqual(case["initial_state"]["future_target"], "not-created")
                    self.assertEqual(
                        case["initial_state"]["target_generation"],
                        "forbidden-during-qualification",
                    )

    def test_project_local_rule_uses_its_real_verification_entry(self):
        source = FIXTURE_ROOT / "project-local-rule" / "project"
        case = load_case("project-local-rule")
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            shutil.copytree(source, project)
            command = case["initial_state"]["verification_command"]

            self.assertEqual(run_entry(project, command).returncode, 0)
            (project / "src" / "generated" / "client.txt").write_text(
                "manual-edit\n",
                encoding="utf-8",
            )
            self.assertEqual(run_entry(project, command).returncode, 2)

    def test_shared_skill_contexts_expose_distinct_real_entries(self):
        case_root = FIXTURE_ROOT / "shared-skill"

        alpha = case_root / "contexts" / "alpha"
        alpha_contract = json.loads(
            (alpha / ".agents" / "verification.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [run_entry(alpha, item["command"]).returncode for item in alpha_contract["required_checks"]],
            [0, 0],
        )

        beta = case_root / "contexts" / "beta"
        beta_contract = json.loads(
            (beta / "project-verification.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [run_entry(beta, item["argv"]).returncode for item in beta_contract["checks"]],
            [0, 4],
        )

    def test_project_local_skill_uses_public_entry_on_a_temporary_copy(self):
        source = FIXTURE_ROOT / "project-local-skill" / "project"
        case = load_case("project-local-skill")
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            shutil.copytree(source, project)
            entry = case["initial_state"]["public_entry"]

            self.assertEqual(run_entry(project, [*entry, "check"]).returncode, 3)
            self.assertEqual(run_entry(project, [*entry, "build"]).returncode, 0)
            self.assertEqual(run_entry(project, [*entry, "check"]).returncode, 0)

            (project / "data" / "source.json").write_text("{", encoding="utf-8")
            self.assertEqual(run_entry(project, [*entry, "check"]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
