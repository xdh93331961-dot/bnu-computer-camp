# -*- coding: utf-8 -*-
"""Unit tests for scripts/parser.py using real HelloGitHub fixtures."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts import parser  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def load_fixture(issue_id):
    path = os.path.join(FIXTURES, "HelloGitHub%03d.md" % issue_id)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ExtractUrlTest(unittest.TestCase):
    def test_tracking_link_unwrapped(self):
        link = ("https://hellogithub.com/periodical/statistics/click"
                "?target=https://github.com/henrypp/simplewall")
        self.assertEqual(parser.extract_url(link), "https://github.com/henrypp/simplewall")

    def test_plain_link_unchanged(self):
        self.assertEqual(parser.extract_url("https://github.com/foo/bar"),
                         "https://github.com/foo/bar")

    def test_tracking_link_without_target(self):
        link = "https://hellogithub.com/periodical/statistics/click?utm=x"
        self.assertEqual(parser.extract_url(link), link)


class MdToTextTest(unittest.TestCase):
    def test_inline_link_stripped(self):
        self.assertEqual(parser.md_to_text("详见[中文文档](https://ant.design)"),
                         "详见中文文档")

    def test_bold_italic_code(self):
        self.assertEqual(parser.md_to_text("**重点** 和 `code` 与 *斜体*"),
                         "重点 和 code 与 斜体")

    def test_image_replaced_with_alt(self):
        self.assertEqual(parser.md_to_text("![截图](https://x/y.png) 说明"),
                         "截图 说明")


class Issue124Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue = parser.parse_issue(load_fixture(124), 124)

    def test_title(self):
        self.assertEqual(self.issue["title"], "《HelloGitHub》第 124 期")

    def test_categories_and_counts(self):
        expected = [
            ("C 项目", 2), ("C# 项目", 2), ("C++ 项目", 1), ("Go 项目", 4),
            ("Java 项目", 1), ("JavaScript 项目", 5), ("Python 项目", 5),
            ("Rust 项目", 2), ("Skills", 3), ("Swift 项目", 3),
            ("人工智能", 5), ("其它", 5), ("开源书籍", 2),
        ]
        got = [(c["name"], len(c["projects"])) for c in self.issue["categories"]]
        self.assertEqual(got, expected)

    def test_first_project(self):
        proj = self.issue["categories"][0]["projects"][0]
        self.assertEqual(proj["name"], "86Box")
        self.assertEqual(proj["url"], "https://github.com/86Box/86Box")
        self.assertTrue(proj["description"].startswith("复古 PC 模拟器"))
        self.assertEqual(proj["author"], "")

    def test_no_html_leak(self):
        for cat in self.issue["categories"]:
            for proj in cat["projects"]:
                self.assertNotIn("<p", proj["description"])
                self.assertNotIn("<img", proj["description"])

    def test_all_github_urls(self):
        for cat in self.issue["categories"]:
            for proj in cat["projects"]:
                self.assertTrue(proj["url"].startswith("https://github.com/"), proj["url"])


class Issue100Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue = parser.parse_issue(load_fixture(100), 100)

    def test_c_and_csharp_separate(self):
        names = [c["name"] for c in self.issue["categories"]]
        self.assertIn("C 项目", names)
        self.assertIn("C# 项目", names)
        self.assertIn("Kotlin 项目", names)

    def test_counts(self):
        expected = [
            ("C 项目", 2), ("C# 项目", 4), ("C++ 项目", 1), ("Go 项目", 4),
            ("Java 项目", 3), ("JavaScript 项目", 5), ("Kotlin 项目", 1),
            ("Python 项目", 5), ("Rust 项目", 3), ("Swift 项目", 2),
            ("人工智能", 3), ("其它", 6), ("开源书籍", 2),
        ]
        got = [(c["name"], len(c["projects"])) for c in self.issue["categories"]]
        self.assertEqual(got, expected)

    def test_multi_line_code_block_description(self):
        # issue 100 entry 7 (diff-pdf) contains a fenced code block
        cats = {c["name"]: c["projects"] for c in self.issue["categories"]}
        cpp = cats["C++ 项目"]
        self.assertEqual(cpp[0]["name"], "diff-pdf")
        self.assertIn("diff-pdf --output-diff", cpp[0]["description"])


class Issue1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue = parser.parse_issue(load_fixture(1), 1)

    def test_categories(self):
        expected = [
            ("CSS 项目", 1), ("JavaScript 项目", 3), ("Python 项目", 4),
            ("其它", 4), ("开源书籍", 5),
        ]
        got = [(c["name"], len(c["projects"])) for c in self.issue["categories"]]
        self.assertEqual(got, expected)


class OldCompactFormatTest(unittest.TestCase):
    """The parser should tolerate the older "compact" issue flavor."""

    SAMPLE = (
        "# 《HelloGitHub》第 43 期 > 兴趣是最好的老师，**HelloGitHub** 让你对开源感兴趣！\n"
        "\n"
        "关注「HelloGitHub」公众号，第一时间收到推送\n"
        "\n"
        "### JavaScript 项目 2、[activate-power-mode]"
        "(https://hellogithub.com/periodical/statistics/click?target=https://github.com/disjukr/activate-power-mode)"
        "：爆炸输入效果，[在线演示](http://example.com/demo)\n"
        "\n"
        "### Python 项目\n"
        "3、[tqdm](https://hellogithub.com/periodical/statistics/click?target=https://github.com/tqdm/tqdm)"
        "：进度条库，示例代码：\n"
        "```python\n"
        "from tqdm import tqdm\n"
        "for i in tqdm(range(10)):\n"
        "    pass\n"
        "```\n"
        "4、[Minos](https://hellogithub.com/periodical/statistics/click?target=https://github.com/phith0n/Minos)"
        "：一个基于 Tornado/MongoDB/Redis 的社区系统 来自 [@面条](https://hellogithub.com/user/qi74Zp23wYKeAVB) 的分享\n"
        "\n"
        "『上一期』 | 反馈和建议 | 『下一期』\n"
        "\n"
        "👉 来！推荐开源项目 👈\n"
    )

    def test_compact_format(self):
        issue = parser.parse_issue(self.SAMPLE, 43)
        self.assertEqual(issue["title"], "《HelloGitHub》第 43 期")
        cats = {c["name"]: c["projects"] for c in issue["categories"]}
        self.assertEqual(len(cats["JavaScript 项目"]), 1)
        self.assertEqual(cats["JavaScript 项目"][0]["name"], "activate-power-mode")
        self.assertEqual(cats["JavaScript 项目"][0]["url"],
                         "https://github.com/disjukr/activate-power-mode")
        self.assertIn("在线演示", cats["JavaScript 项目"][0]["description"])
        self.assertNotIn("http://example.com/demo", cats["JavaScript 项目"][0]["description"])

        python = cats["Python 项目"]
        self.assertEqual([p["name"] for p in python], ["tqdm", "Minos"])
        self.assertIn("from tqdm import tqdm", python[0]["description"])
        self.assertEqual(python[1]["author"], "面条")

    def test_leading_entry_before_heading(self):
        sample = (
            "# 《HelloGitHub》第 50 期\n"
            "2、[gnucash](https://hellogithub.com/periodical/statistics/click?target=https://github.com/Gnucash/gnucash)"
            "：完全开源的财务软件。\n"
            "### C# 项目\n"
            "3、[Lean](https://hellogithub.com/periodical/statistics/click?target=https://github.com/QuantConnect/Lean)"
            "：量化引擎。\n"
        )
        issue = parser.parse_issue(sample, 50)
        cats = {c["name"]: c["projects"] for c in issue["categories"]}
        self.assertEqual(len(cats["未分类"]), 1)
        self.assertEqual(cats["未分类"][0]["name"], "gnucash")
        self.assertEqual(len(cats["C# 项目"]), 1)


class TrailingSectionsTest(unittest.TestCase):
    def test_sponsor_and_license_stopped(self):
        sample = (
            "# 《HelloGitHub》第 60 期\n"
            "### Go 项目\n"
            "1、[kage](https://hellogithub.com/periodical/statistics/click?target=https://github.com/tamnd/kage)"
            "：把网站打包离线阅读。\n"
            "## 赞助\n"
            "<table><tr><td>sponsor ad</td></tr></table>\n"
            "## 声明\n"
            "本作品采用 CC BY-NC-ND 4.0 许可\n"
        )
        issue = parser.parse_issue(sample, 60)
        cats = {c["name"]: c["projects"] for c in issue["categories"]}
        self.assertEqual(list(cats.keys()), ["Go 项目"])
        self.assertEqual(len(cats["Go 项目"]), 1)
        self.assertNotIn("sponsor ad", cats["Go 项目"][0]["description"])


if __name__ == "__main__":
    unittest.main()