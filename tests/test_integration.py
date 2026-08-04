# -*- coding: utf-8 -*-
"""Full-data integration tests.

Two layers:
  * offline: validate the committed data/issues.json structure (no network).
  * online : rebuild the dataset from the HelloGitHub repo and validate the
             same invariants (skipped automatically when the network is down).
"""

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ISSUES_PATH = os.path.join(ROOT, "data", "issues.json")
MIN_ISSUES = 124
LATEST_EXPECTED = 124


def load_committed():
    with open(ISSUES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def validate_dataset(data):
    issues = data["issues"]
    assert len(issues) >= MIN_ISSUES, "expected >= %d issues, got %d" % (MIN_ISSUES, len(issues))
    ids = [issue["id"] for issue in issues]
    assert ids == sorted(ids), "issue ids must be sorted"
    assert max(ids) == LATEST_EXPECTED, "latest issue should be %d" % LATEST_EXPECTED

    for issue in issues:
        assert issue["title"], "issue %d missing title" % issue["id"]
        assert issue["categories"], "issue %d has no categories" % issue["id"]
        for cat in issue["categories"]:
            assert cat["name"], "issue %d has unnamed category" % issue["id"]
            assert cat["projects"], "issue %d category %r is empty" % (issue["id"], cat["name"])
            for proj in cat["projects"]:
                assert proj["name"], "project missing name in issue %d" % issue["id"]
                assert proj["url"].startswith("https://github.com/"), (
                    "bad url %r in issue %d" % (proj["url"], issue["id"]))
                assert proj["description"], "project %r missing description" % proj["name"]
    return len(issues), sum(len(c["projects"]) for i in issues for c in i["categories"])


class CommittedDataTest(unittest.TestCase):
    def test_committed_dataset(self):
        data = load_committed()
        n_issues, n_projects = validate_dataset(data)
        self.assertGreaterEqual(n_issues, MIN_ISSUES)
        self.assertGreater(n_projects, 4000)


class OnlineRebuildTest(unittest.TestCase):
    def test_rebuild_from_repo(self):
        from scripts import build_data
        try:
            files = build_data.fetch_issues("tarball")
        except Exception as exc:  # noqa: BLE001
            self.skipTest("network unavailable: %r" % exc)
        data = build_data.build_data(files)
        n_issues, n_projects = validate_dataset(data)
        self.assertGreaterEqual(n_issues, MIN_ISSUES)
        self.assertGreater(n_projects, 4000)


if __name__ == "__main__":
    unittest.main()