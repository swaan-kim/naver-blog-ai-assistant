import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_hub  # noqa: E402


BRIEF = '''---
post_id: "series-hub"
selected_title: "AI 냠냠 글 모아보기"
title_status: "approved"
outline_status: "approved"
final_status: "pending"
---

## 목차

1. 첫 목차
2. 둘째 목차
3. 셋째 목차
'''

DRAFT = '''---
post_id: "series-hub"
title: "AI 냠냠 글 모아보기"
format: "AI 냠냠 목차"
category: "AI 냠냠"
tags: ["AI냠냠"]
cover_image: "media/cover.png"
images: ["media/cover.png"]
ai_media: "true"
hub_url: ""
previous_url: ""
pair_url: ""
content_index_path: "../content-index.json"
cta: "질문을 남겨주세요."
status: "draft"
outline_approved: "true"
final_approved: "false"
sources: []
---

도입입니다. 쉬운 설명을 모읍니다. 필요한 글을 골라 읽습니다.

{{image:cover}}

## 첫 목차

새 글을 연결합니다. 질문부터 고릅니다.

## 둘째 목차

직접 확인한 후기를 연결합니다. 한계를 함께 적습니다.

## 셋째 목차

자료를 확인한 글을 연결합니다. 질문을 남겨주세요.
'''

DRAFT = DRAFT.replace(
    "새 글을 연결합니다. 질문부터 고릅니다.",
    "새 글을 질문별로 연결해 처음 온 독자도 필요한 내용을 찾게 하고 " * 9 + "마칩니다.",
).replace(
    "직접 확인한 후기를 연결합니다. 한계를 함께 적습니다.",
    "직접 확인한 후기에는 편한 점과 막힌 점, 다시 쓸 조건을 함께 적고 " * 9 + "마칩니다.",
).replace(
    "자료를 확인한 글을 연결합니다. 질문을 남겨주세요.",
    "공식 자료와 한계를 확인한 글을 연결하고 독자의 질문도 함께 모아 " * 9 + "질문을 남겨주세요.",
)


class HubValidationTests(unittest.TestCase):
    def write_hub(self, root: Path, brief: str = BRIEF, draft: str = DRAFT) -> tuple[Path, Path]:
        hub_dir = root / "hub"
        (hub_dir / "media").mkdir(parents=True)
        (hub_dir / "brief.md").write_text(brief, encoding="utf-8")
        (hub_dir / "draft.md").write_text(draft, encoding="utf-8")
        (hub_dir / "media" / "cover.png").write_bytes(b"cover")
        index = {"hub": {"title": "AI 냠냠 글 모아보기", "draft_path": "hub/draft.md", "status": "draft", "url": ""}}
        index_path = root / "content-index.json"
        index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        return hub_dir, index_path

    def test_prepare_passes_after_title_and_outline_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            hub_dir, index_path = self.write_hub(Path(temp))
            result = validate_hub.validate_hub(hub_dir, index_path, "prepare")

        self.assertTrue(result["ok"], result)

    def test_prepare_blocks_pending_title_and_outline(self) -> None:
        brief = BRIEF.replace('title_status: "approved"', 'title_status: "pending"').replace('outline_status: "approved"', 'outline_status: "pending"')
        draft = DRAFT.replace('outline_approved: "true"', 'outline_approved: "false"')
        with tempfile.TemporaryDirectory() as temp:
            hub_dir, index_path = self.write_hub(Path(temp), brief, draft)
            result = validate_hub.validate_hub(hub_dir, index_path, "prepare")

        codes = {item["code"] for item in result["errors"]}
        self.assertIn("TITLE_NOT_APPROVED", codes)
        self.assertIn("OUTLINE_NOT_APPROVED", codes)

    def test_publish_needs_final_approval_and_final_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            hub_dir, index_path = self.write_hub(Path(temp))
            result = validate_hub.validate_hub(hub_dir, index_path, "publish")

        codes = {item["code"] for item in result["errors"]}
        self.assertIn("FINAL_NOT_APPROVED", codes)
        self.assertIn("DRAFT_NOT_FINAL", codes)
