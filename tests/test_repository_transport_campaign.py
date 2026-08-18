import tempfile
import unittest
from pathlib import Path

from tools.repository_transport_campaign import (
    COUNTS,
    algorithm_totals,
    changed_paths,
    erik_metrics,
    materialize,
    parse_rsync_stats,
    rrdp_metrics,
    run,
)

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local"


class RepositoryTransportCampaignTest(unittest.TestCase):
    def setUp(self):
        # The campaign only resets directories below the ignored local/ tree,
        # which is absent from a clean checkout.
        LOCAL.mkdir(exist_ok=True)

    def test_algorithm_totals_preserve_confirmed_endpoints(self):
        totals = algorithm_totals()
        self.assertEqual(totals["rsa-2048"], 1_768_736)
        self.assertEqual(totals["composite-mldsa65-p256"], 9_797_552)
        self.assertGreater(totals["ml-dsa-65"], totals["rsa-2048"])
        self.assertLess(totals["ml-dsa-65"], totals["composite-mldsa65-p256"])

    def test_scenarios_have_expected_changed_sets(self):
        self.assertEqual(len(changed_paths("one_roa_update")), 3)
        self.assertEqual(len(changed_paths("ten_percent_roa_churn")), 102)

    def test_rrdp_and_erik_request_shapes(self):
        with tempfile.TemporaryDirectory(dir=LOCAL) as directory:
            root = Path(directory) / "source"
            materialize(root, "rsa-2048", "baseline", set())
            cold_rrdp = rrdp_metrics(root, "cold_sync", 1)
            self.assertEqual(cold_rrdp["request_count"], 2)
            self.assertGreater(cold_rrdp["response_body_bytes"], algorithm_totals()["rsa-2048"])
            unchanged = erik_metrics(root, "rsa-2048", "unchanged_repository", "baseline")
            self.assertEqual(unchanged["tree_fetch"]["request_count"], 1)
            update = erik_metrics(root, "rsa-2048", "one_roa_update", "one-roa")
            self.assertEqual(update["tree_fetch"]["request_count"], 5)
            cold = erik_metrics(root, "rsa-2048", "cold_sync", "baseline")
            self.assertEqual(cold["tree_fetch"]["request_count"], 2 + sum(COUNTS.values()))
            self.assertEqual(cold["snapshot_prefetch"]["request_count"], 1)

    def test_rsync_stats_parse_on_both_rsync_implementations(self):
        openrsync = (
            "Number of files: 3\n"
            "Number of files transferred: 2\n"
            "Total transferred file size: 9 B\n"
            "File list size: 143 B\n"
            "Total sent: 264 B\n"
            "Total received: 64 B\n"
        )
        gnu_rsync = (
            "Number of files: 3 (reg: 2, dir: 1)\n"
            "Number of created files: 2 (reg: 2)\n"
            "Number of deleted files: 0\n"
            "Number of regular files transferred: 2\n"
            "Total file size: 9 bytes\n"
            "Total transferred file size: 9 bytes\n"
            "Literal data: 9 bytes\n"
            "Matched data: 0 bytes\n"
            "File list size: 143\n"
            "File list generation time: 0.001 seconds\n"
            "File list transfer time: 0.000 seconds\n"
            "Total bytes sent: 264\n"
            "Total bytes received: 64\n"
            "\n"
            "sent 264 bytes  received 64 bytes  656.00 bytes/sec\n"
            "total size is 9  speedup is 0.03\n"
        )
        expected = {
            "files_transferred": 2,
            "object_bytes": 9,
            "file_list_bytes": 143,
            "sent_bytes": 264,
            "received_bytes": 64,
        }
        summary_only = (
            "Number of regular files transferred: 2\n"
            "Total transferred file size: 9 bytes\n"
            "File list size: 143\n"
            "\n"
            "sent 264 bytes  received 64 bytes  656.00 bytes/sec\n"
        )
        self.assertEqual(parse_rsync_stats(openrsync), expected)
        self.assertEqual(parse_rsync_stats(gnu_rsync), expected)
        # An unrecognized byte-total label still resolves via the summary line.
        self.assertEqual(parse_rsync_stats(summary_only), expected)
        with self.assertRaises(ValueError):
            parse_rsync_stats("Number of files transferred: 2\n")
        with self.assertRaises(ValueError):
            parse_rsync_stats(
                "Total bytes sent: 264\nTotal bytes received: 64\n"
            )

    def test_rsync_repetitions_restore_each_scenario_baseline(self):
        with tempfile.TemporaryDirectory(dir=LOCAL) as directory:
            result = run(Path(directory) / "campaign", repetitions=2)
            rsa = result["algorithms"]["rsa-2048"]["scenarios"]
            self.assertEqual(rsa["cold_sync"]["rsync"]["files_transferred"], sum(COUNTS.values()))
            self.assertEqual(rsa["unchanged_repository"]["rsync"]["files_transferred"], 0)
            self.assertEqual(rsa["one_roa_update"]["rsync"]["files_transferred"], 3)
            self.assertEqual(rsa["ten_percent_roa_churn"]["rsync"]["files_transferred"], 102)
