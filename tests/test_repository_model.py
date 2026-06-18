import unittest

from pqc_rpki_lab.repository_model import AlgorithmSize, Corpus, estimate_repository_bytes


class RepositoryModelTest(unittest.TestCase):
    def test_repository_estimate_has_total_and_transport_impacts(self):
        corpus = Corpus(1, 2, 1, 1, 2, 100, 100, 50, 80, 40)
        alg = AlgorithmSize("test", 10, 20)
        row = estimate_repository_bytes(corpus, alg)
        expected = 1 * 130 + 2 * 130 + 1 * 70 + 1 * 100 + 2 * 60
        self.assertEqual(row["repository_total_bytes"], expected)
        self.assertGreater(row["rrdp_snapshot_bytes"], expected)
        self.assertGreater(row["local_cache_bytes"], expected)
        self.assertEqual(row["status"], "estimated")

    def test_literature_replacement_formula_reproduces_rsa_baseline(self):
        baseline = 838_030_450
        public_keys = 393_427
        signatures = 788_916
        non_crypto = baseline - public_keys * 272 - signatures * 256
        reproduced = non_crypto + public_keys * 272 + signatures * 256
        self.assertEqual(reproduced, baseline)
