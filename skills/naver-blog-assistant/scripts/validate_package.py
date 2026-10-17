#!/usr/bin/env python3
"""Validate an AI 냠냠 brief, draft, and shared content index compactly."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import validate_draft


FORMATS = {"3분 AI 정리", "직접 써봤습니다", "자료를 확인해봤습니다"}
TOPIC_TYPES = {"trend", "evergreen"}
USAGE_LEVELS = {"처음 써봄", "몇 번 써봄", "계속 쓰는 중"}
RISK_LEVELS = {"standard", "high-stakes"}
BRIEF_FIELDS = (
    "post_id",
    "topic_type",
    "format",
    "risk_level",
    "reader_question",
    "why_now",
    "work_relevance",
    "evidence_level",
    "follow_up_check",
    "duplicate_check",
    "selected_on",
    "source_date",
    "usage_level",
    "goal_note",
    "convenience_note",
    "friction_note",
    "reuse_note",
    "topic_status",
    "outline_status",
    "final_status",
    "primary_sources",
    "independent_sources",
)
MAX_PROBLEMS = 20


def problem(code: str, message: str, file: str) -> dict[str, str]:
    return {"code": code, "message": message[:240], "file": file}


def read_text(path: Path, errors: list[dict[str, str]]) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        errors.append(problem("FILE_UNREADABLE", f"Cannot read {path.name}.", path.name))
        return None


def parse_frontmatter(
    text: str | None, filename: str, errors: list[dict[str, str]]
) -> tuple[dict[str, Any], list[str]]:
    if text is None:
        return {}, []
    try:
        metadata, body, _ = validate_draft.parse_document(text)
        return metadata, body
    except validate_draft.FrontmatterError as exc:
        errors.append(problem("FRONTMATTER_INVALID", str(exc), filename))
        return {}, []


def nonempty_string(metadata: dict[str, Any], field: str) -> bool:
    value = metadata.get(field)
    return isinstance(value, str) and bool(value.strip())


def section_bullets(lines: list[str], heading: str) -> list[str]:
    items: list[str] = []
    active = False
    for line in lines:
        if line.startswith("## "):
            active = line.strip() == f"## {heading}"
            continue
        if active and line.lstrip().startswith("-"):
            item = line.lstrip()[1:].strip()
            if item:
                items.append(item)
    return items


def draft_headings(lines: list[str]) -> list[str]:
    return [line[3:].strip() for line in lines if line.startswith("## ") and line[3:].strip()]


def source_is_placeholder(value: str) -> bool:
    candidate = value.split("|", 1)[-1].strip()
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme not in {"http", "https"}
        or not host
        or host in {"example.com", "example.org", "example.net", "localhost"}
        or "YOUR_" in candidate.upper()
        or "TODO" in candidate.upper()
    )


def validate_brief(
    metadata: dict[str, Any], body: list[str], stage: str, errors: list[dict[str, str]]
) -> None:
    for field in BRIEF_FIELDS:
        if field not in metadata:
            errors.append(problem("BRIEF_FIELD_MISSING", f"Missing brief field: {field}", "brief.md"))

    for field in BRIEF_FIELDS:
        if field in {"primary_sources", "independent_sources"}:
            continue
        if field in metadata and not nonempty_string(metadata, field):
            errors.append(problem("BRIEF_FIELD_INVALID", f"{field} must be non-empty.", "brief.md"))

    article_format = metadata.get("format")
    if article_format not in FORMATS:
        errors.append(problem("FORMAT_INVALID", "Use one of the three AI 냠냠 formats.", "brief.md"))
    if metadata.get("topic_type") not in TOPIC_TYPES:
        errors.append(problem("TOPIC_TYPE_INVALID", "topic_type must be trend or evergreen.", "brief.md"))
    if metadata.get("risk_level") not in RISK_LEVELS:
        errors.append(
            problem(
                "RISK_LEVEL_INVALID",
                "risk_level must be standard or high-stakes.",
                "brief.md",
            )
        )

    for field in ("primary_sources", "independent_sources"):
        value = metadata.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            errors.append(problem("BRIEF_FIELD_INVALID", f"{field} must be a string list.", "brief.md"))
        elif any(source_is_placeholder(item) for item in value):
            errors.append(
                problem(
                    "SOURCE_PLACEHOLDER",
                    f"Replace template or invalid URLs in {field}.",
                    "brief.md",
                )
            )

    primary = metadata.get("primary_sources", [])
    independent = metadata.get("independent_sources", [])
    if isinstance(primary, list) and not primary:
        errors.append(problem("PRIMARY_SOURCE_MISSING", "At least one primary source is required.", "brief.md"))
    if metadata.get("risk_level") == "high-stakes":
        primary_prefixes = ("official|", "paper|", "public-agency|")
        has_official = isinstance(primary, list) and any(
            isinstance(item, str) and item.startswith(primary_prefixes)
            for item in primary
        )
        has_independent = isinstance(independent, list) and any(
            isinstance(item, str) and item.startswith("independent|")
            for item in independent
        )
        if not has_official:
            errors.append(
                problem(
                    "OFFICIAL_SOURCE_MISSING",
                    "High-stakes topics require an official, paper, or public-agency source.",
                    "brief.md",
                )
            )
        if not has_independent:
            errors.append(
                problem(
                    "INDEPENDENT_SOURCE_MISSING",
                    "High-stakes topics require a reliable independent source.",
                    "brief.md",
                )
            )

    if metadata.get("topic_type") == "trend":
        try:
            selected = date.fromisoformat(str(metadata.get("selected_on", "")))
            source = date.fromisoformat(str(metadata.get("source_date", "")))
            age = (selected - source).days
            if age < 0 or age > 14:
                errors.append(
                    problem(
                        "SOURCE_DATE_OUT_OF_RANGE",
                        "A trend source must be dated within 14 days before selection.",
                        "brief.md",
                    )
                )
        except ValueError:
            errors.append(problem("DATE_INVALID", "Use ISO dates (YYYY-MM-DD).", "brief.md"))

    if article_format == "직접 써봤습니다":
        if metadata.get("usage_level") not in USAGE_LEVELS:
            errors.append(
                problem(
                    "USAGE_LEVEL_INVALID",
                    "Use 처음 써봄, 몇 번 써봄, or 계속 쓰는 중.",
                    "brief.md",
                )
            )
        for field in ("goal_note", "convenience_note", "friction_note", "reuse_note"):
            value = metadata.get(field, "")
            if not isinstance(value, str) or not value.strip() or value == "해당 없음":
                errors.append(
                    problem(
                        "OWNER_NOTE_MISSING",
                        f"A direct-use post needs the owner's {field}.",
                        "brief.md",
                    )
                )

    if metadata.get("topic_status") != "approved":
        errors.append(problem("TOPIC_NOT_APPROVED", "The owner has not approved the topic.", "brief.md"))
    if metadata.get("outline_status") != "approved":
        errors.append(problem("OUTLINE_NOT_APPROVED", "The owner has not approved the outline.", "brief.md"))
    if stage == "publish" and metadata.get("final_status") != "approved":
        errors.append(problem("FINAL_NOT_APPROVED", "The owner has not approved the final text.", "brief.md"))

    outline = section_bullets(body, "승인된 목차")
    expected = (3, 4) if article_format == "3분 AI 정리" else (4, 5)
    if not expected[0] <= len(outline) <= expected[1]:
        errors.append(
            problem(
                "OUTLINE_COUNT_INVALID",
                f"The approved outline needs {expected[0]}-{expected[1]} items.",
                "brief.md",
            )
        )


def load_index(path: Path, errors: list[dict[str, str]]) -> dict[str, Any]:
    text = read_text(path, errors)
    if text is None:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        errors.append(problem("INDEX_JSON_INVALID", "content-index.json is invalid JSON.", path.name))
        return {}
    if not isinstance(value, dict):
        errors.append(problem("INDEX_SCHEMA_INVALID", "The index root must be an object.", path.name))
        return {}
    return value


def validate_index(
    index: dict[str, Any], brief: dict[str, Any], draft: dict[str, Any], errors: list[dict[str, str]]
) -> dict[str, int]:
    if (
        index.get("schema_version") != 1
        or index.get("category") != "AI 냠냠"
        or index.get("managed_by") != "ai-namnyam-pilot"
    ):
        errors.append(problem("INDEX_SCHEMA_INVALID", "Use schema version 1 and category AI 냠냠.", "content-index.json"))

    hub = index.get("hub")
    if not isinstance(hub, dict) or hub.get("status") != "published" or not hub.get("url"):
        errors.append(problem("HUB_NOT_PUBLISHED", "Publish the new-series hub before a pilot post.", "content-index.json"))

    posts = index.get("posts")
    if not isinstance(posts, list):
        errors.append(problem("INDEX_SCHEMA_INVALID", "posts must be a list.", "content-index.json"))
        return {"trend": 0, "evergreen": 0}

    post_id = brief.get("post_id")
    matches = [item for item in posts if isinstance(item, dict) and item.get("post_id") == post_id]
    if len(matches) != 1:
        errors.append(problem("INDEX_POST_MISMATCH", "The current post must appear exactly once in the index.", "content-index.json"))
    else:
        item = matches[0]
        for field in ("format", "topic_type"):
            if item.get(field) != brief.get(field):
                errors.append(problem("INDEX_POST_MISMATCH", f"Index {field} does not match brief.md.", "content-index.json"))
        if item.get("title") != draft.get("title"):
            errors.append(problem("INDEX_POST_MISMATCH", "Index title does not match draft.md.", "content-index.json"))

    previous_published = [
        item
        for item in posts
        if isinstance(item, dict)
        and item.get("post_id") != post_id
        and item.get("status") == "published"
        and item.get("url")
    ]
    expected_previous = previous_published[-1]["url"] if previous_published else ""
    if draft.get("previous_url", "") != expected_previous:
        errors.append(
            problem(
                "PREVIOUS_LINK_MISMATCH",
                "draft previous_url must point to the latest published new-series post.",
                "draft.md",
            )
        )
    if isinstance(hub, dict) and draft.get("hub_url") != hub.get("url"):
        errors.append(problem("HUB_LINK_MISMATCH", "draft hub_url must match the index hub URL.", "draft.md"))

    counts = {"trend": 0, "evergreen": 0}
    for item in posts:
        if isinstance(item, dict) and item.get("topic_type") in counts:
            counts[item["topic_type"]] += 1
    return counts


def validate_package(post_dir: Path, index_path: Path, stage: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    brief_path = post_dir / "brief.md"
    draft_path = post_dir / "draft.md"
    brief_text = read_text(brief_path, errors)
    draft_text = read_text(draft_path, errors)
    for filename, payload in (("brief.md", brief_text), ("draft.md", draft_text)):
        if payload is not None and validate_draft.SECRET_RE.search(payload):
            errors.append(
                problem(
                    "POSSIBLE_SECRET",
                    "Remove possible API keys or access credentials.",
                    filename,
                )
            )
    brief, brief_body = parse_frontmatter(brief_text, "brief.md", errors)
    draft, draft_body = parse_frontmatter(draft_text, "draft.md", errors)
    draft_sources = draft.get("sources", []) if draft else []
    if isinstance(draft_sources, list) and any(
        isinstance(item, str) and source_is_placeholder(item)
        for item in draft_sources
    ):
        errors.append(
            problem(
                "SOURCE_PLACEHOLDER",
                "Replace template or invalid URLs in draft sources.",
                "draft.md",
            )
        )

    if brief:
        validate_brief(brief, brief_body, stage, errors)
        approved_outline = section_bullets(brief_body, "승인된 목차")
        actual_headings = draft_headings(draft_body)
        if approved_outline and actual_headings != approved_outline:
            errors.append(
                problem(
                    "OUTLINE_ORDER_MISMATCH",
                    "The draft headings must exactly match the approved outline and order.",
                    "draft.md",
                )
            )
    draft_result: dict[str, Any] = {}
    if draft_text is not None:
        draft_result = validate_draft.validate_text(draft_text)
        errors.extend(
            problem(item["code"], item["message"], "draft.md")
            for item in draft_result.get("errors", [])
        )
        warnings.extend(
            problem(item["code"], item["message"], "draft.md")
            for item in draft_result.get("warnings", [])
        )

    if brief and draft:
        for field in ("post_id", "format"):
            if brief.get(field) != draft.get(field):
                errors.append(problem("BRIEF_DRAFT_MISMATCH", f"{field} differs between files.", "draft.md"))
        if stage == "publish" and draft.get("status") != "final-approved":
            errors.append(problem("DRAFT_NOT_FINAL", "Set draft status to final-approved after review.", "draft.md"))

    index = load_index(index_path, errors)
    try:
        index_text = index_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        index_text = ""
    if index_text and validate_draft.SECRET_RE.search(index_text):
        errors.append(
            problem(
                "POSSIBLE_SECRET",
                "Remove possible API keys or access credentials.",
                "content-index.json",
            )
        )
    mix = validate_index(index, brief, draft, errors) if index and brief and draft else {"trend": 0, "evergreen": 0}
    if mix["trend"] + mix["evergreen"] == 8 and mix != {"trend": 6, "evergreen": 2}:
        warnings.append(
            problem(
                "PILOT_MIX_DEVIATION",
                "The eight-post pilot differs from the six trend / two evergreen target.",
                "content-index.json",
            )
        )

    summary = draft_result.get("summary", {})
    return {
        "ok": not errors,
        "stage": stage,
        "summary": {
            "post_id": str(brief.get("post_id", ""))[:120],
            "title": str(draft.get("title", ""))[:120],
            "format": str(brief.get("format", ""))[:40],
            "body_chars": summary.get("body_chars", 0),
            "headings": summary.get("headings", 0),
            "paragraphs": summary.get("paragraphs", 0),
            "unresolved_markers": summary.get("unresolved_markers", 0),
            "trend_posts": mix["trend"],
            "evergreen_posts": mix["evergreen"],
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors[:MAX_PROBLEMS],
        "warnings": warnings[:MAX_PROBLEMS],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_dir", type=Path, help="Directory containing brief.md and draft.md")
    parser.add_argument("--index", required=True, type=Path, help="Shared content-index.json")
    parser.add_argument("--stage", choices=("prepare", "publish"), default="prepare")
    parser.add_argument("--json", action="store_true", help="Compatibility flag; JSON is the default")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    result = validate_package(args.post_dir, args.index, args.stage)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            separators=None if args.pretty else (",", ":"),
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
