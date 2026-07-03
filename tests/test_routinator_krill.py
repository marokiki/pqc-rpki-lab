import tempfile
import unittest
from pathlib import Path

from pqc_rpki_lab.routinator_krill import (
    KRILL_SPEC,
    ROUTINATOR_ENV,
    ROUTINATOR_SPEC,
    binary_probe,
    extension_map,
    scan_project,
)
from tools.routinator_krill_interop import matrix_row


class RoutinatorKrillTest(unittest.TestCase):
    def test_unset_source_env_is_skipped(self):
        result = scan_project(ROUTINATOR_SPEC, {})
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["source_env"], ROUTINATOR_ENV)

    def test_fake_rust_checkout_is_identified(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "Cargo.toml").write_text('[package]\nname = "routinator"\nversion = "0.0.0"\n')
            (root / "src").mkdir()
            (root / "src" / "validation.rs").write_text("// validation extension point\n")
            result = scan_project(ROUTINATOR_SPEC, {ROUTINATOR_ENV: str(root)})
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["cargo_package"], "routinator")
        self.assertIn("src/validation.rs", result["likely_files"])

    def test_extension_map_lists_both_projects(self):
        projects = {row["project"] for row in extension_map()["projects"]}
        self.assertEqual(projects, {"Routinator", "Krill"})

    def test_unset_binary_env_is_skipped(self):
        result = binary_probe(KRILL_SPEC, {})
        self.assertEqual(result["status"], "skipped")

    def test_interop_matrix_separates_validation_layers(self):
        probe = {
            "project": "Routinator",
            "role": "validator",
            "status": "confirmed",
            "reason": "",
        }
        row = matrix_row(probe, "rsa-baseline", "")
        self.assertEqual(row["parser"], "skipped")
        self.assertEqual(row["signature"], "skipped")
        self.assertEqual(row["certificate_path"], "skipped")
        self.assertEqual(row["manifest"], "skipped")
        self.assertEqual(row["vrp_output"], "skipped")

