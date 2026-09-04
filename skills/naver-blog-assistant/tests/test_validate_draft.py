import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_draft  # noqa: E402


def make_draft(
    body: str,
    *,
    title: str = "AI 블로그 자동화를 안전하게 시작하는 법",
    tags: tuple[str, ...] = ("AI잡학냠냠", "AI기초", "자동화"),
) -> str:
    tag_lines = "\n".join(f'  - "{tag}"' for tag in tags)
    return (
        "---\n"
        f'title: "{title}"\n'
        'category: "AI·AX 잡학 냠냠"\n'
        "tags:\n"
        f"{tag_lines}\n"
        "images: []\n"
        "---\n\n"
        f"{body}\n"
    )


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["errors"]}


class DraftValidationTests(unittest.TestCase):
    def test_valid_draft_returns_compact_summary(self) -> None:
        body = (
            "이 글은 독자가 겪는 문제를 쉽게 풀어냅니다.\n\n"
            "## 핵심 개념\n\n"
            "어려운 개념을 짧고 직관적으로 설명합니다.\n\n"
            "## 실행 순서\n\n"
            "1. 필요한 정보를 확인합니다.\n"
            "2. 결과를 검증합니다."
        )
        result = validate_draft.validate_text(
            make_draft(body), min_chars=20, max_chars=500, min_headings=2, max_headings=2
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"]["headings"], 2)
        self.assertEqual(result["summary"]["paragraphs"], 2)
        self.assertNotIn("body", result)
        self.assertNotIn(body, json.dumps(result, ensure_ascii=False))

    def test_frontmatter_requires_all_fields(self) -> None:
        text = "---\ntitle: \"제목\"\ncategory: \"카테고리\"\ntags: []\n---\n\n한글 본문\n"
        result = validate_draft.validate_text(text, min_chars=1, max_chars=100)

        self.assertFalse(result["ok"])
        self.assertIn("FIELD_MISSING", codes(result))

    def test_malformed_frontmatter_returns_one_compact_error(self) -> None:
        result = validate_draft.validate_text("---\ntitle: [broken\n---\n비밀 본문")

        self.assertFalse(result["ok"])
        self.assertEqual([item["code"] for item in result["errors"]], ["FRONTMATTER_INVALID"])
        self.assertEqual(result["warnings"], [])

    def test_duplicate_title_line_is_rejected(self) -> None:
        title = "AI 블로그 자동화를 안전하게 시작하는 법"
        body = f"{title}\n\n본문은 여기서 시작합니다."
        result = validate_draft.validate_text(
            make_draft(body, title=title), min_chars=1, max_chars=500
        )

        self.assertIn("TITLE_DUPLICATED_IN_BODY", codes(result))
        self.assertEqual(result["summary"]["title_in_body"], 1)

    def test_body_length_limits_and_hangul_are_validated(self) -> None:
        short = validate_draft.validate_text(make_draft("짧음"), min_chars=10, max_chars=20)
        long = validate_draft.validate_text(make_draft("가" * 21), min_chars=10, max_chars=20)
        no_hangul = validate_draft.validate_text(make_draft("English only text"), min_chars=1, max_chars=50)

        self.assertIn("BODY_TOO_SHORT", codes(short))
        self.assertIn("BODY_TOO_LONG", codes(long))
        self.assertIn("BODY_NO_HANGUL", codes(no_hangul))

    def test_heading_and_paragraph_spacing_are_validated(self) -> None:
        body = "첫 문단\n## 붙은 소제목\n둘째 문단\n셋째 문단"
        result = validate_draft.validate_text(make_draft(body), min_chars=1, max_chars=500)

        self.assertIn("HEADING_SPACE_BEFORE", codes(result))
        self.assertIn("HEADING_SPACE_AFTER", codes(result))
        self.assertIn("PARAGRAPH_SPACING", codes(result))
        spacing_lines = [
            item["line"] for item in result["errors"] if item["code"] == "PARAGRAPH_SPACING"
        ]
        self.assertTrue(all(isinstance(line, int) for line in spacing_lines))

    def test_duplicate_tags_ignore_hash_and_case(self) -> None:
        result = validate_draft.validate_text(
            make_draft("한글 본문", tags=("AI", "#ai")), min_chars=1, max_chars=100
        )

        self.assertIn("TAG_DUPLICATE", codes(result))

    def test_cli_emits_one_line_json_without_body(self) -> None:
        unique_body = "한글 비밀 본문 XYZ-DO-NOT-ECHO"
        with tempfile.TemporaryDirectory() as temp_dir:
            draft_path = Path(temp_dir) / "draft.md"
            draft_path.write_text(make_draft(unique_body), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = validate_draft.main(
                    [
                        str(draft_path),
                        "--min-chars",
                        "1",
                        "--max-chars",
                        "100",
                        "--min-headings",
                        "0",
                        "--json",
                    ]
                )

        rendered = output.getvalue().strip()
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(rendered.splitlines()), 1)
        self.assertNotIn(unique_body, rendered)
        self.assertTrue(json.loads(rendered)["ok"])

    def test_json_size_is_bounded_for_many_layout_errors_and_long_title(self) -> None:
        long_title = "제목" * 1_000
        many_unspaced_lines = "\n".join("한글 문단" for _ in range(5_000))
        result = validate_draft.validate_text(
            make_draft(many_unspaced_lines, title=long_title),
            min_chars=1,
            max_chars=100_000,
        )
        rendered = json.dumps(result, ensure_ascii=False, separators=(",", ":"))

        self.assertGreater(result["summary"]["error_count"], len(result["errors"]))
        self.assertLessEqual(len(result["errors"]), validate_draft.MAX_REPORTED_PROBLEMS)
        self.assertTrue(result["summary"]["title_truncated"])
        self.assertLess(len(rendered), 5_000)

    def test_default_heading_range_and_custom_override(self) -> None:
        def body_with_sections(count: int) -> str:
            sections = "\n\n".join(
                f"## 소제목 {index}\n\n한글 설명 {index}" for index in range(1, count + 1)
            )
            return f"도입 문단\n\n{sections}"

        default_result = validate_draft.validate_text(
            make_draft(body_with_sections(3)), min_chars=1, max_chars=500
        )
        default_valid = validate_draft.validate_text(
            make_draft(body_with_sections(4)), min_chars=1, max_chars=500
        )
        default_too_many = validate_draft.validate_text(
            make_draft(body_with_sections(7)), min_chars=1, max_chars=500
        )
        custom_result = validate_draft.validate_text(
            make_draft(body_with_sections(3)),
            min_chars=1,
            max_chars=500,
            min_headings=3,
            max_headings=3,
        )

        self.assertIn("HEADINGS_TOO_FEW", codes(default_result))
        self.assertTrue(default_valid["ok"])
        self.assertIn("HEADINGS_TOO_MANY", codes(default_too_many))
        self.assertTrue(custom_result["ok"])

    def test_invalid_quotes_are_rejected(self) -> None:
        text = (
            '---\ntitle: "bad\\q"\ncategory: "카테고리"\n'
            'tags: ["AI"]\nimages: []\n---\n\n한글 본문'
        )
        result = validate_draft.validate_text(text)

        self.assertEqual([item["code"] for item in result["errors"]], ["FRONTMATTER_INVALID"])

    def test_unindented_block_lists_are_supported(self) -> None:
        text = (
            '---\ntitle: "제목"\ncategory: "카테고리"\ntags:\n- "AI"\n'
            'images: []\nsources: []\n---\n\n한글 본문'
        )
        result = validate_draft.validate_text(
            text, min_chars=1, max_chars=100, min_headings=0, max_headings=6
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["tags"], 1)

    def test_optional_sources_must_be_a_string_list(self) -> None:
        text = (
            '---\ntitle: "제목"\ncategory: "카테고리"\ntags: ["AI"]\n'
            'images: []\nsources: "https://example.com"\n---\n\n한글 본문'
        )
        result = validate_draft.validate_text(
            text, min_chars=1, max_chars=100, min_headings=0, max_headings=6
        )

        self.assertIn("FIELD_INVALID", codes(result))

    def test_bundled_template_requires_real_title_and_category(self) -> None:
        template = (
            Path(__file__).resolve().parents[1] / "assets" / "draft-template.md"
        ).read_text(encoding="utf-8")
        metadata, _, _ = validate_draft.parse_document(template)
        result = validate_draft.validate_text(template, min_chars=1, max_chars=1_000)

        self.assertFalse(result["ok"])
        self.assertEqual(metadata["title"], "")
        self.assertEqual(metadata["category"], "")
        messages = [
            item["message"] for item in result["errors"] if item["code"] == "FIELD_INVALID"
        ]
        self.assertTrue(any("title" in message for message in messages))
        self.assertTrue(any("category" in message for message in messages))

    def test_unclosed_fence_is_rejected(self) -> None:
        body = "도입 문단\n\n```text\n닫히지 않은 코드"
        result = validate_draft.validate_text(
            make_draft(body), min_chars=1, max_chars=500, min_headings=0, max_headings=6
        )

        self.assertIn("MARKDOWN_FENCE_UNCLOSED", codes(result))

    def test_nested_title_is_found_but_code_example_is_ignored(self) -> None:
        title = "AI 블로그 자동화를 안전하게 시작하는 법"
        nested = validate_draft.validate_text(
            make_draft(f"> ## {title}\n\n한글 본문", title=title),
            min_chars=1,
            max_chars=500,
            min_headings=0,
            max_headings=6,
        )
        code_only = validate_draft.validate_text(
            make_draft(f"한글 본문\n\n```text\n{title}\n```", title=title),
            min_chars=1,
            max_chars=500,
            min_headings=0,
            max_headings=6,
        )

        self.assertIn("TITLE_DUPLICATED_IN_BODY", codes(nested))
        self.assertNotIn("TITLE_DUPLICATED_IN_BODY", codes(code_only))

    def test_table_without_outer_pipes_does_not_trigger_paragraph_spacing(self) -> None:
        body = "도입 문단\n\n항목 | 설명\n--- | ---\nAPI | 통로"
        result = validate_draft.validate_text(
            make_draft(body), min_chars=1, max_chars=500, min_headings=0, max_headings=6
        )

        self.assertNotIn("PARAGRAPH_SPACING", codes(result))


if __name__ == "__main__":
    unittest.main()
