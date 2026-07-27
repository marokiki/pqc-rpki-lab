from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name: str):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompositeE2ETests(unittest.TestCase):
    def test_generator_registers_exact_composite_suite(self) -> None:
        generator = load_tool("generate_rpki_objects")
        rows = {slug: (display, provider) for display, slug, provider, _ in generator.ALGORITHMS}
        self.assertEqual(
            rows["composite-mldsa65-p256"],
            ("ML-DSA-65 + ECDSA P-256", "MLDSA65-ECDSA-P256-SHA512"),
        )

    def test_private_defaults_stay_below_local(self) -> None:
        e2e = load_tool("composite_e2e")
        negative = load_tool("composite_negative_tests")
        benchmark = load_tool("composite_e2e_benchmark")
        for path in (e2e.DEFAULT_OUTPUT, negative.DEFAULT_OUTPUT, benchmark.LOCAL):
            self.assertTrue(path.is_relative_to(ROOT / "local"), path)

    def test_mixed_tree_configuration_has_required_boundary(self) -> None:
        e2e = load_tool("composite_e2e")
        text = e2e.ca_config(
            ROOT / "local" / "test-ca",
            certificate=ROOT / "local" / "test-ca.pem",
            private_key=ROOT / "local" / "test-ca.key",
        )
        self.assertIn("URI:rsync://example.invalid/repository/ta.cer", text)
        self.assertIn("URI:rsync://example.invalid/repository/child/child.mft", text)
        self.assertIn("crl_extensions=crl_ext", text)
        self.assertIn("string_mask=default", text)

    def test_measurement_summary_is_small_scale_and_complete(self) -> None:
        path = ROOT / "results" / "composite-e2e" / "benchmark-summary.json"
        summary = json.loads(path.read_text())
        self.assertEqual(summary["generation_repetitions"], 100)
        self.assertEqual(summary["validation_repetitions"], 1000)
        self.assertIn("not real-repository", summary["classification"])
        scenarios = {
            "rsa-baseline",
            "pure-mldsa65",
            "composite-standalone",
            "rsa-to-composite-mixed",
        }
        self.assertEqual(set(summary["generation"]), scenarios)
        self.assertEqual(set(summary["validation"]), scenarios)
        for phase in ("generation", "validation"):
            for scenario in scenarios:
                for metric in ("wall_seconds", "cpu_seconds", "max_rss_kib"):
                    self.assertEqual(
                        set(summary[phase][scenario][metric]),
                        {"median", "stdev", "min", "max"},
                    )
        for scenario in scenarios:
            self.assertEqual(
                set(summary["generation"][scenario]["artifact_total_bytes"]),
                {"median", "stdev", "min", "max"},
            )

    def test_generated_directory_requires_safe_marked_location(self) -> None:
        from pqc_rpki_lab.workspace import reset_generated_directory

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with self.assertRaises(ValueError):
                reset_generated_directory(root, allowed_root=root)
            unmarked = root / "unmarked"
            unmarked.mkdir()
            with self.assertRaises(ValueError):
                reset_generated_directory(unmarked, allowed_root=root)
            generated = reset_generated_directory(
                root / "generated", allowed_root=root
            )
            (generated / "data").write_text("replace me")
            reset_generated_directory(generated, allowed_root=root)
            self.assertFalse((generated / "data").exists())

    def test_negative_summary_has_machine_readable_reason_codes(self) -> None:
        path = ROOT / "results" / "composite-e2e" / "negative-summary.json"
        summary = json.loads(path.read_text())
        self.assertTrue(summary["all_rejected"])
        self.assertEqual(len(summary["results"]), 12)
        for result in summary["results"]:
            self.assertTrue(result["reason_code"])
            self.assertTrue(result["rejected"])
            self.assertNotIn("stdout", result)
            self.assertNotIn("stderr", result)


if __name__ == "__main__":
    unittest.main()
