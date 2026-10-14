"""Tests for README badge rendering and round-trip."""

from __future__ import annotations

# Scripts are not installed as a package; import by path.
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from convert_toml_to_readme import render_readme  # noqa: E402
from readme_to_toml import MarkdownParser, generate_toml  # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


SAMPLE_TOML_NO_BASIC = """
course_name = "示例课程"
course_code = "LANG1001"
repo_type = "normal"
description = "课程简介"

[[sections]]
title = "章节"
[[sections.items]]
content = "正文"
"""

SAMPLE_TOML_WITH_BASIC = (
    'course_name = "示例课程"\n'
    'course_code = "LANG1001"\n'
    'repo_type = "normal"\n'
    "\n"
    "[[sections]]\n"
    'title = "基本信息"\n'
    "[[sections.items]]\n"
    'content = """\n'
    "【学分】: 2\n"
    "【成绩构成】: 作业 40% | 期末考试 60%\n"
    '"""\n'
    "\n"
    "[[sections]]\n"
    'title = "章节"\n'
    "[[sections.items]]\n"
    'content = "正文"\n'
)

README_WITH_GRADES_SUMMARY_BADGES = """\
# LANG1001 - 示例课程
<!-- TOML-META: repo_type="normal" -->
<!-- TOML-BADGES: source="grades_summary" -->

![成绩构成](https://img.shields.io/badge/%E6%88%90%E7%BB%A9%E6%9E%84%E6%88%90-gold)
![作业40%](https://img.shields.io/badge/%E4%BD%9C%E4%B8%9A-40%25-wheat)

课程简介

## 章节
<!-- TOML-SECTION: title="章节" -->

<!-- TOML-ITEM: id="item-章节-1" -->

正文
"""


class TestReadmeBadges(unittest.TestCase):
    def test_no_badges_without_basic_info_section(self) -> None:
        data = tomllib.loads(SAMPLE_TOML_NO_BASIC)
        md = render_readme(data)
        self.assertNotIn("TOML-BADGES", md)
        self.assertNotIn("shields.io", md)

    def test_badges_from_basic_info_section(self) -> None:
        data = tomllib.loads(SAMPLE_TOML_WITH_BASIC)
        md = render_readme(data)
        self.assertIn('<!-- TOML-BADGES: source="basic_info" -->', md)
        self.assertIn("学分", md)
        self.assertIn("成绩构成", md)
        self.assertNotIn("基本信息", md)

    def test_reverse_skips_grades_summary_badges(self) -> None:
        doc = MarkdownParser(README_WITH_GRADES_SUMMARY_BADGES).parse()
        self.assertEqual(doc.credits, "")
        self.assertEqual(doc.grading, "")
        toml_out = generate_toml(doc)
        self.assertNotIn("基本信息", toml_out)

    def test_round_trip_basic_info(self) -> None:
        data = tomllib.loads(SAMPLE_TOML_WITH_BASIC)
        md = render_readme(data)
        doc = MarkdownParser(md).parse()
        toml_out = generate_toml(doc)
        data2 = tomllib.loads(toml_out)
        md2 = render_readme(data2)
        self.assertEqual(md.strip(), md2.strip())

    def test_grades_summary_file_does_not_inject_badges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "grades_summary.toml").write_text(
                """
[grades.LANG1001]
[grades.LANG1001.default.default]
grade = "作业 100%"
""",
                encoding="utf-8",
            )
            toml_path = root / "readme.toml"
            toml_path.write_text(SAMPLE_TOML_NO_BASIC, encoding="utf-8")
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            md = render_readme(data)
            self.assertNotIn("shields.io", md)


if __name__ == "__main__":
    unittest.main()
