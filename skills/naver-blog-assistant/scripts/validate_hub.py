#!/usr/bin/env python3
"""Validate the AI 냠냠 series hub without returning its body."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import validate_draft


MAX_PROBLEMS = 16
REQUIRED_BRIEF_FIELDS = (
    "post_id",
    "selected_title",
    "title_status",
    "outline_status",
    "final_status",
)


def problem(code: str, message: str, file: str) -> dict[str, str]:
    return {"code": code, "message": message[:240], "file": file}


def _read(path: Path, errors: list[dict[str, str]]) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        errors.append(problem("FILE_UNREADABLE", f"Cannot read {path.name}.", path.name))
        return None


def _parse(text: str | None, filename: str, errors: list[dict[str, str]]) -> tuple[dict[str, Any], list[str]]:
    if text is None:
        return {}, []
    try:
        metadata, body, _ = validate_draft.parse_document(text)
        return metadata, body
    except validate_draft.FrontmatterError as exc:
        errors.append(problem("FRONTMATTER_INVALID", str(exc), filename))
        return {}, []


def _numbered_items(lines: list[str], heading: str) -> list[str]:
    import re

    active = False
    items: list[str] = []
    for line in lines:
        if line.startswith("## "):
            active = line.strip() == f"## {heading}"
            continue
        if active:
            match = re.match(r"^\s*\d+[.)]\s+(.+?)\s*$", line)
            if match:
                items.append(match.group(1))
    return items


def validate_hub(hub_dir: Path, index_path: Path, stage: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    brief_text = _read(hub_dir / "brief.md", errors)
    draft_text = _read(hub_dir / "draft.md", errors)
    brief, brief_body = _parse(brief_text, "brief.md", errors)
    draft, draft_body = _parse(draft_text, "draft.md", errors)

    for field in REQUIRED_BRIEF_FIELDS:
        value = brief.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(problem("BRIEF_FIELD_INVALID", f"Missing or empty {field}.", "brief.md"))
    for field in ("title_status", "outline_status", "final_status"):
        if brief.get(field) not in {"pending", "approved"}:
            errors.append(problem("APPROVAL_STATUS_INVALID", f"{field} must be pending or approved.", "brief.md"))

    if brief.get("title_status") != "approved":
        errors.append(problem("TITLE_NOT_APPROVED", "The hub title is not approved.", "brief.md"))
    if brief.get("outline_status") != "approved":
        errors.append(problem("OUTLINE_NOT_APPROVED", "The hub outline is not approved.", "brief.md"))
    if stage == "publish" and brief.get("final_status") != "approved":
        errors.append(problem("FINAL_NOT_APPROVED", "The hub final text is not approved.", "brief.md"))

    outline = _numbered_items(brief_body, "목차")
    headings = [line[3:].strip() for line in draft_body if line.startswith("## ")]
    if outline != headings:
        errors.append(problem("OUTLINE_ORDER_MISMATCH", "Hub headings must match the brief outline.", "draft.md"))
    if brief.get("post_id") != draft.get("post_id") or brief.get("selected_title") != draft.get("title"):
        errors.append(problem("BRIEF_DRAFT_MISMATCH", "Hub id or title differs between files.", "draft.md"))

    draft_result: dict[str, Any] = {}
    if draft_text is not None:
        draft_result = validate_draft.validate_text(draft_text)
        errors.extend(problem(item["code"], item["message"], "draft.md") for item in draft_result.get("errors", []))
        warnings.extend(problem(item["code"], item["message"], "draft.md") for item in draft_result.get("warnings", []))
    if stage == "publish" and draft.get("status") != "final-approved":
        errors.append(problem("DRAFT_NOT_FINAL", "Set hub draft status to final-approved after review.", "draft.md"))
    expected_outline_flag = "true" if brief.get("outline_status") == "approved" else "false"
    if draft.get("outline_approved") != expected_outline_flag:
        errors.append(problem("APPROVAL_FLAG_MISMATCH", "draft outline_approved does not match brief.md.", "draft.md"))
    expected_final_flag = "true" if brief.get("final_status") == "approved" else "false"
    if draft.get("final_approved") != expected_final_flag:
        errors.append(problem("APPROVAL_FLAG_MISMATCH", "draft final_approved does not match brief.md.", "draft.md"))

    try:
        index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        index = {}
        errors.append(problem("INDEX_INVALID", "Cannot read a valid content-index.json.", index_path.name))
    hub = index.get("hub", {}) if isinstance(index, dict) else {}
    if not isinstance(hub, dict) or hub.get("title") != draft.get("title") or hub.get("draft_path") != "hub/draft.md":
        errors.append(problem("INDEX_HUB_MISMATCH", "Index hub record does not match the draft.", index_path.name))
    cover = draft.get("cover_image", "")
    cover_path = (hub_dir / cover).resolve() if isinstance(cover, str) else hub_dir
    try:
        cover_path.relative_to(hub_dir.resolve())
    except ValueError:
        errors.append(problem("MEDIA_PATH_INVALID", "Hub cover must stay inside the hub folder.", "draft.md"))
    else:
        if not cover_path.is_file():
            errors.append(problem("MEDIA_FILE_MISSING", "Hub cover file is missing.", "draft.md"))

    summary = draft_result.get("summary", {})
    return {
        "ok": not errors,
        "stage": stage,
        "summary": {
            "post_id": str(draft.get("post_id", ""))[:120],
            "title": str(draft.get("title", ""))[:120],
            "body_chars": summary.get("body_chars", 0),
            "headings": summary.get("headings", 0),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors[:MAX_PROBLEMS],
        "warnings": warnings[:MAX_PROBLEMS],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hub_dir", type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--stage", choices=("prepare", "publish"), default="prepare")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = validate_hub(args.hub_dir, args.index, args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, separators=None if args.pretty else (",", ":")))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
