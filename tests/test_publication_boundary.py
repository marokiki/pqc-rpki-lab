import unittest

from tools.pre_publication_check import classify, classify_content


class PublicationBoundaryTest(unittest.TestCase):
    def test_local_tree_is_not_public(self):
        self.assertIsNotNone(classify("local/reviewer-context.md"))
        self.assertIsNotNone(classify("tmp/cache/secret.txt"))
        self.assertIsNotNone(classify("scratch/plan.md"))

    def test_review_only_filename_is_not_public(self):
        self.assertIsNotNone(classify("docs/mailing-list-feedback.md"))
        self.assertIsNotNone(classify("docs/reviewer-thread-summary.md"))
        self.assertIsNotNone(classify("docs/upstream-notes.md"))
        self.assertIsNotNone(classify("docs/wip-patch-routinator.md"))

    def test_public_measurement_paths_are_allowed(self):
        self.assertIsNone(classify("results/object-benchmarks/object-benchmarks.json"))
        self.assertIsNone(classify("docs/draft-01-technical-changes.md"))
        self.assertIsNone(classify("testdata/mixed-tree/topology.json"))

    def test_private_key_patterns_are_not_public(self):
        self.assertIsNotNone(classify("testdata/rsa/ta.key"))
        self.assertIsNotNone(classify("testdata/rsa/ta.private.pem"))

    def test_private_content_is_not_public(self):
        self.assertIsNotNone(classify_content(b"-----BEGIN " + b"PRIVATE KEY-----\n"))
        self.assertIsNotNone(classify_content(b"/" + b"Users/example/private/cache"))
        self.assertIsNotNone(classify_content(b"/var/" + b"folders/example/private/cache"))
        self.assertIsNone(classify_content(b"public reproducible result\n"))
