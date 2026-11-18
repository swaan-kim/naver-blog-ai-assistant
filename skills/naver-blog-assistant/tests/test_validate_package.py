import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_package  # noqa: E402


def brief_text(*, final_status: str = "pending", usage: bool = False) -> str:
    article_format = "직접 써봤습니다" if usage else "3분 AI 정리"
    usage_level = "처음 써봄" if usage else "해당 없음"
    note = "직접 확인한 메모" if usage else "해당 없음"
    outline_count = 4 if usage else 3
    outline = "\n".join(f"- 승인 소제목 {index}" for index in range(outline_count))
    return f'''---
post_id: "2026-10-18-test"
topic_type: "trend"
format: "{article_format}"
risk_level: "standard"
reader_question: "이 발표가 내 일에 어떤 의미인가요?"
primary_query: "AI 발표 직장인 의미"
reader_reward: "지금 써볼지 기다릴지 결정합니다."
owner_angle: "공식 발표를 비개발자 업무 장면으로 풉니다."
next_link_plan: "목차에서 관련 사용 후기로 연결합니다."
selected_title: "직장인을 위한 AI 발표 쉽게 읽기"
why_now: "새 공식 발표가 나왔습니다."
work_relevance: "직장인의 도구 선택에 영향을 줍니다."
evidence_level: "공식 발표 확인"
follow_up_check: "다음 버전에서 다시 확인"
duplicate_check: "기존 글과 겹치지 않음"
selected_on: "2026-10-18"
source_date: "2026-10-10"
usage_level: "{usage_level}"
goal_note: "{note}"
convenience_note: "{note}"
friction_note: "{note}"
reuse_note: "{note}"
topic_status: "approved"
outline_status: "approved"
final_status: "{final_status}"
primary_sources: ["official|https://openai.com/index/introducing-chatgpt-search"]
independent_sources: []
---

## 제목 후보

1. 직장인을 위한 AI 발표 쉽게 읽기
2. 제목 둘
3. 제목 셋

## 승인된 목차

{outline}

## 사실·경험·해석

- 확인한 사실
'''


def draft_text(*, final: bool = False, usage: bool = False) -> str:
    article_format = "직접 써봤습니다" if usage else "3분 AI 정리"
    heading_count = 4 if usage else 3
    repeat = 110 if usage else 75
    body = "도입입니다.\n\n{{image:cover}}\n\n" + "\n\n".join(
        f"## 승인 소제목 {index}\n\n" + ("한글설명" * repeat)
        for index in range(heading_count)
    ) + (
        "\n\n{{image:evidence}}\n\n"
        "목차: https://blog.naver.com/hub\n\n"
        "공식 발표를 직접 확인해보세요."
    )
    status = "final-approved" if final else "draft"
    return f'''---
post_id: "2026-10-18-test"
title: "직장인을 위한 AI 발표 쉽게 읽기"
format: "{article_format}"
category: "AI 냠냠"
tags: ["AI냠냠", "AI발표"]
cover_image: "cover.png"
evidence_image: "evidence.png"
images: ["cover.png", "evidence.png"]
ai_media: "false"
sources: ["official|https://openai.com/index/introducing-chatgpt-search"]
content_index_path: "../content-index.json"
hub_url: "https://blog.naver.com/hub"
previous_url: ""
pair_url: ""
cta: "공식 발표를 직접 확인해보세요."
status: "{status}"
---

{body}
'''


def index_data(*, title: str = "직장인을 위한 AI 발표 쉽게 읽기") -> dict:
    return {
        "schema_version": 1,
        "series": "AI 냠냠",
        "category": "AI 냠냠",
        "managed_by": "ai-namnyam-pilot",
        "hub": {
            "title": "AI 냠냠 글 모아보기",
            "status": "published",
            "url": "https://blog.naver.com/hub",
        },
        "pilot": {"target_posts": 8, "trend_target": 6, "evergreen_target": 2},
        "posts": [
            {
                "post_id": "2026-10-18-test",
                "title": title,
                "format": "3분 AI 정리",
                "topic_type": "trend",
                "status": "draft",
                "url": "",
            }
        ],
    }


def add_frontmatter(text: str, extra: str) -> str:
    prefix, frontmatter, body = text.split("---\n", 2)
    return f"{prefix}---\n{frontmatter}{extra}---\n{body}"


def v2_package() -> tuple[str, str, dict]:
    checked = date.today()
    publish_by = checked + timedelta(days=7)
    fresh_until = checked + timedelta(days=90)
    source_url = "https://openai.com/index/introducing-chatgpt-search"
    brief = add_frontmatter(
        brief_text(),
        (
            'reader_role: "기획·마케팅·운영 실무자"\n'
            'reader_problem: "AI 결과를 실제 업무로 연결하기 어렵습니다."\n'
            'content_role: "entry"\n'
            'cluster_id: "repeat-work"\n'
            'one_line_answer: "작은 업무 흐름부터 검증합니다."\n'
            'unique_proof: "직접 만든 전후 비교표"\n'
            f'facts_checked_at: "{checked.isoformat()}"\n'
            f'publish_by: "{publish_by.isoformat()}"\n'
            f'claim_source_map: ["핵심 기능|{source_url}|{checked.isoformat()}|배포 범위는 달라질 수 있음"]\n'
        ),
    )
    draft = add_frontmatter(
        draft_text(),
        (
            'reading_minutes: "3"\n'
            'one_line_answer: "작은 업무 흐름부터 검증합니다."\n'
            'internal_toc: ["승인 소제목 0", "승인 소제목 1", "승인 소제목 2"]\n'
            'evidence_source: "owner-created"\n'
            f'evidence_captured_at: "{checked.isoformat()}"\n'
            'evidence_use_basis: "owner-created"\n'
            'evidence_ai_edited: "false"\n'
            'recommended_next_id: ""\n'
            'recommended_next_label: "다음 실전 글을 읽습니다."\n'
            f'facts_checked_at: "{checked.isoformat()}"\n'
        ),
    )
    index = index_data()
    index["schema_version"] = 2
    index["posts"][0].update(
        {
            "cluster_id": "repeat-work",
            "content_role": "entry",
            "recommended_next_id": "",
            "published_at": "",
            "facts_checked_at": checked.isoformat(),
            "freshness_due": fresh_until.isoformat(),
            "source_hash": "sha256:test",
            "d7_review": "pending",
            "d28_review": "pending",
            "publishing_state": "draft",
            "legacy_excluded": False,
        }
    )
    return brief, draft, index


class PackageValidationTests(unittest.TestCase):
    def write_package(
        self, root: Path, *, brief: str, draft: str, index: dict
    ) -> tuple[Path, Path]:
        post_dir = root / "post"
        post_dir.mkdir()
        (post_dir / "brief.md").write_text(brief, encoding="utf-8")
        (post_dir / "draft.md").write_text(draft, encoding="utf-8")
        (post_dir / "cover.png").write_bytes(b"cover")
        (post_dir / "evidence.png").write_bytes(b"evidence")
        index_path = root / "content-index.json"
        index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        return post_dir, index_path

    def test_prepare_package_passes_without_final_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief_text(), draft=draft_text(), index=index_data()
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["summary"]["unresolved_markers"], 0)

    def test_proposal_passes_without_owner_approval_or_published_hub(self) -> None:
        brief = (
            brief_text()
            .replace('topic_status: "approved"', 'topic_status: "pending"')
            .replace('outline_status: "approved"', 'outline_status: "pending"')
            .replace("## 승인된 목차", "## 제안 목차")
        )
        draft = (
            draft_text()
            .replace('hub_url: "https://blog.naver.com/hub"', 'hub_url: ""')
            .replace('status: "draft"', 'status: "proposal"')
            .replace("목차: https://blog.naver.com/hub\n\n", "")
        )
        index = index_data()
        index["hub"] = {"title": "AI 냠냠 글 모아보기", "status": "draft", "url": ""}
        index["posts"][0]["status"] = "proposal"
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief, draft=draft, index=index
            )
            result = validate_package.validate_package(post_dir, index_path, "proposal")

        self.assertTrue(result["ok"], result)

    def test_proposal_cannot_skip_prepare_approval_gate(self) -> None:
        brief = (
            brief_text()
            .replace('topic_status: "approved"', 'topic_status: "pending"')
            .replace('outline_status: "approved"', 'outline_status: "pending"')
            .replace("## 승인된 목차", "## 제안 목차")
        )
        draft = (
            draft_text()
            .replace('hub_url: "https://blog.naver.com/hub"', 'hub_url: ""')
            .replace('status: "draft"', 'status: "proposal"')
            .replace("목차: https://blog.naver.com/hub\n\n", "")
        )
        index = index_data()
        index["hub"] = {"title": "AI 냠냠 글 모아보기", "status": "draft", "url": ""}
        index["posts"][0]["status"] = "proposal"
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief, draft=draft, index=index
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        result_codes = {item["code"] for item in result["errors"]}
        self.assertIn("TOPIC_NOT_APPROVED", result_codes)
        self.assertIn("HUB_NOT_PUBLISHED", result_codes)
        self.assertIn("DRAFT_NOT_READY", result_codes)

    def test_publish_requires_final_approval_and_final_draft_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief_text(), draft=draft_text(), index=index_data()
            )
            blocked = validate_package.validate_package(post_dir, index_path, "publish")
            (post_dir / "brief.md").write_text(
                brief_text(final_status="approved"), encoding="utf-8"
            )
            (post_dir / "draft.md").write_text(draft_text(final=True), encoding="utf-8")
            allowed = validate_package.validate_package(post_dir, index_path, "publish")

        blocked_codes = {item["code"] for item in blocked["errors"]}
        self.assertIn("FINAL_NOT_APPROVED", blocked_codes)
        self.assertIn("DRAFT_NOT_FINAL", blocked_codes)
        self.assertTrue(allowed["ok"], allowed)

    def test_direct_use_post_requires_four_owner_notes(self) -> None:
        index = index_data()
        index["posts"][0]["format"] = "직접 써봤습니다"
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp),
                brief=brief_text(usage=True).replace('goal_note: "직접 확인한 메모"', 'goal_note: "해당 없음"'),
                draft=draft_text(usage=True),
                index=index,
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        self.assertIn("OWNER_NOTE_MISSING", {item["code"] for item in result["errors"]})

    def test_unresolved_marker_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp),
                brief=brief_text(),
                draft=draft_text() + "\n[[확인 필요]]\n",
                index=index_data(),
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        self.assertIn("UNRESOLVED_MARKER", {item["code"] for item in result["errors"]})

    def test_draft_headings_must_match_approved_outline_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp),
                brief=brief_text(),
                draft=draft_text().replace("## 승인 소제목 1", "## 다른 소제목", 1),
                index=index_data(),
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        self.assertIn(
            "OUTLINE_ORDER_MISMATCH", {item["code"] for item in result["errors"]}
        )

    def test_title_source_and_media_consistency_are_enforced(self) -> None:
        cases = {
            "title": (
                brief_text().replace(
                    'selected_title: "직장인을 위한 AI 발표 쉽게 읽기"',
                    'selected_title: "다른 제목"',
                ),
                draft_text(),
                None,
                "SELECTED_TITLE_MISMATCH",
            ),
            "sources": (
                brief_text(),
                draft_text().replace(
                    'sources: ["official|https://openai.com/index/introducing-chatgpt-search"]',
                    'sources: ["official|https://openai.com/index/introducing-chatgpt-search", "official|https://openai.com/security"]',
                ),
                None,
                "SOURCE_LIST_MISMATCH",
            ),
            "media": (
                brief_text(),
                draft_text(),
                "evidence.png",
                "MEDIA_FILE_MISSING",
            ),
        }
        for name, (brief, draft, missing, expected) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                post_dir, index_path = self.write_package(
                    Path(temp), brief=brief, draft=draft, index=index_data()
                )
                if missing:
                    (post_dir / missing).unlink()
                result = validate_package.validate_package(post_dir, index_path, "prepare")

            self.assertIn(expected, {item["code"] for item in result["errors"]})

    def test_risk_level_is_an_enum_and_template_sources_are_rejected(self) -> None:
        brief = brief_text().replace(
            'risk_level: "standard"', 'risk_level: "high"'
        ).replace(
            "https://openai.com/index/introducing-chatgpt-search",
            "https://example.com",
        )
        draft = draft_text().replace(
            "https://openai.com/index/introducing-chatgpt-search",
            "https://example.com",
        )
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief, draft=draft, index=index_data()
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        result_codes = {item["code"] for item in result["errors"]}
        self.assertIn("RISK_LEVEL_INVALID", result_codes)
        self.assertIn("SOURCE_PLACEHOLDER", result_codes)

    def test_secrets_are_scanned_in_all_three_package_files(self) -> None:
        secret = "github_pat_" + "A" * 30
        for target in ("brief", "draft", "index"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                brief = brief_text() + (secret if target == "brief" else "")
                draft = draft_text() + (secret if target == "draft" else "")
                index = index_data()
                if target == "index":
                    index["credential"] = secret
                post_dir, index_path = self.write_package(
                    Path(temp), brief=brief, draft=draft, index=index
                )
                result = validate_package.validate_package(
                    post_dir, index_path, "prepare"
                )

            self.assertIn(
                "POSSIBLE_SECRET", {item["code"] for item in result["errors"]}
            )

    def test_v2_package_validates_evidence_freshness_and_semantic_relation(self) -> None:
        brief, draft, index = v2_package()
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief, draft=draft, index=index
            )
            valid = validate_package.validate_package(post_dir, index_path, "prepare")

            index["posts"][0]["recommended_next_id"] = "missing-post"
            (index_path).write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
            invalid_next = validate_package.validate_package(post_dir, index_path, "prepare")

        self.assertTrue(valid["ok"], valid)
        self.assertIn(
            "NEXT_RELATION_INVALID",
            {item["code"] for item in invalid_next["errors"]},
        )

    def test_v2_stale_publish_window_and_unknown_claim_source_block(self) -> None:
        brief, draft, index = v2_package()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        brief = brief.replace(
            f'publish_by: "{(date.today() + timedelta(days=7)).isoformat()}"',
            f'publish_by: "{yesterday}"',
        ).replace(
            "https://openai.com/index/introducing-chatgpt-search|",
            "https://invalid.example/source|",
            1,
        )
        with tempfile.TemporaryDirectory() as temp:
            post_dir, index_path = self.write_package(
                Path(temp), brief=brief, draft=draft, index=index
            )
            result = validate_package.validate_package(post_dir, index_path, "prepare")

        result_codes = {item["code"] for item in result["errors"]}
        self.assertIn("PUBLISH_WINDOW_INVALID", result_codes)
        self.assertIn("CLAIM_SOURCE_UNKNOWN", result_codes)


if __name__ == "__main__":
    unittest.main()
