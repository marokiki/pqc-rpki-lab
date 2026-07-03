import unittest

from tools.key_roll_benchmark import benchmark_row


class KeyRollBenchmarkTest(unittest.TestCase):
    def test_key_roll_counts_files_and_bytes(self):
        fixtures = [
            {"algorithm": "RSA-2048/SHA-256", "artifact": "CA certificate", "bytes": "1000"},
            {"algorithm": "RSA-2048/SHA-256", "artifact": "EE certificate", "bytes": "500"},
            {"algorithm": "RSA-2048/SHA-256", "artifact": "CRL", "bytes": "200"},
            {"algorithm": "RSA-2048/SHA-256", "artifact": "ROA CMS", "bytes": "700"},
            {"algorithm": "RSA-2048/SHA-256", "artifact": "Manifest CMS", "bytes": "800"},
        ]
        row = benchmark_row("RSA-2048/SHA-256", fixtures, 2, 3, 1, 0, 0, 0)
        self.assertEqual(row["file_count"], 7)
        self.assertEqual(row["output_bytes"], 2 * 1000 + 200 + 800 + 3 * (500 + 700))

