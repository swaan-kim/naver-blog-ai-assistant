#!/usr/bin/env python3
"""Validate an AI 냠냠 brief, draft, and shared content index compactly."""

from __future__ import annotations

import argparse
import json
import re
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
    "primary_query",
    "reader_reward",
    "owner_angle",
    "next_link_plan",
    "selected_title",
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
BRIEF_V2_FIELDS = (
    "reader_role",
    "reader_problem",
    "content_role",
    "cluster_id",
    "one_line_answer",
    "unique_proof",
    "facts_checked_at",
    "publish_by",
    "claim_source_map",
)
CONTENT_ROLES = {"entry", "proof"}
PUBLISHING_STATES = {
    "proposal",
    "draft",
    "prepared",
    "publishing",
    "published",
    "outcome_uncertain",
    "partial_link_update",
    "legacy_excluded",
}
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


def section_numbered_items(lines: list[str], heading: str) -> list[str]:
    items: list[str] = []
    active = False
    for line in lines:
        if line.startswith("## "):
            active = line.strip() == f"## {heading}"
            continue
        if active:
            match = re.match(r"^\s*\d+[.)]\s+(.+?)\s*$", line)
            if match:
                items.append(match.group(1))
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


def iso_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate_claim_source_map(
    value: Any,
    allowed_source_urls: set[str],
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(
            problem(
                "CLAIM_SOURCE_MAP_INVALID",
                "claim_source_map must contain claim|source-url|checked-date|limitation entries.",
                "brief.md",
            )
        )
        return

    for entry in value:
        if not isinstance(entry, str):
            errors.append(
                problem(
                    "CLAIM_SOURCE_MAP_INVALID",
                    "Every claim_source_map entry must be a string.",
                    "brief.md",
                )
            )
            continue
        parts = [part.strip() for part in entry.split("|", 3)]
        if len(parts) != 4 or any(not part for part in parts[:3]):
            errors.append(
                problem(
                    "CLAIM_SOURCE_MAP_INVALID",
                    "Use claim|source-url|checked-date|limitation for every mapped claim.",
                    "brief.md",
                )
            )
            continue
        _, source_url, checked_at, _ = parts
        if source_url not in allowed_source_urls:
            errors.append(
                problem(
                    "CLAIM_SOURCE_UNKNOWN",
                    "Every mapped claim must use a URL from the brief source lists.",
                    "brief.md",
                )
            )
        if iso_date(checked_at) is None:
            errors.append(
                problem(
                    "CLAIM_CHECK_DATE_INVALID",
                    "Mapped claim check dates must use YYYY-MM-DD.",
                    "brief.md",
                )
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

    v2_mode = any(field in metadata for field in BRIEF_V2_FIELDS)
    if v2_mode:
        for field in BRIEF_V2_FIELDS:
            if field not in metadata:
                errors.append(
                    problem("BRIEF_FIELD_MISSING", f"Missing V2 brief field: {field}", "brief.md")
                )
        for field in BRIEF_V2_FIELDS:
            if field == "claim_source_map":
                continue
            if field in metadata and not nonempty_string(metadata, field):
                errors.append(
                    problem("BRIEF_FIELD_INVALID", f"{field} must be non-empty.", "brief.md")
                )
        if metadata.get("content_role") not in CONTENT_ROLES:
            errors.append(
                problem(
                    "CONTENT_ROLE_INVALID",
                    "content_role must be entry or proof.",
                    "brief.md",
                )
            )

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
    if v2_mode:
        allowed_source_urls = {
            item.split("|", 1)[1].strip()
            for source_list in (primary, independent)
            if isinstance(source_list, list)
            for item in source_list
            if isinstance(item, str) and "|" in item
        }
        validate_claim_source_map(metadata.get("claim_source_map"), allowed_source_urls, errors)

        facts_checked = iso_date(metadata.get("facts_checked_at"))
        publish_by = iso_date(metadata.get("publish_by"))
        if facts_checked is None or publish_by is None:
            errors.append(
                problem(
                    "DATE_INVALID",
                    "facts_checked_at and publish_by must use YYYY-MM-DD.",
                    "brief.md",
                )
            )
        elif publish_by < facts_checked:
            errors.append(
                problem(
                    "PUBLISH_WINDOW_INVALID",
                    "publish_by cannot be earlier than facts_checked_at.",
                    "brief.md",
                )
            )
        elif stage in {"prepare", "publish"} and date.today() > publish_by:
            errors.append(
                problem(
                    "FACTS_STALE",
                    "Recheck the facts and move publish_by before preparing or publishing.",
                    "brief.md",
                )
            )
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

    for field in ("topic_status", "outline_status", "final_status"):
        if metadata.get(field) not in {"pending", "approved"}:
            errors.append(
                problem(
                    "APPROVAL_STATUS_INVALID",
                    f"{field} must be pending or approved.",
                    "brief.md",
                )
            )

    if stage in {"prepare", "publish"} and metadata.get("topic_status") != "approved":
        errors.append(problem("TOPIC_NOT_APPROVED", "The owner has not approved the topic.", "brief.md"))
    if stage in {"prepare", "publish"} and metadata.get("outline_status") != "approved":
        errors.append(problem("OUTLINE_NOT_APPROVED", "The owner has not approved the outline.", "brief.md"))
    if stage == "publish" and metadata.get("final_status") != "approved":
        errors.append(problem("FINAL_NOT_APPROVED", "The owner has not approved the final text.", "brief.md"))

    outline_heading = "제안 목차" if stage == "proposal" else "승인된 목차"
    outline = section_bullets(body, outline_heading)
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
    index: dict[str, Any],
    brief: dict[str, Any],
    draft: dict[str, Any],
    stage: str,
    errors: list[dict[str, str]],
) -> dict[str, int]:
    schema_version = index.get("schema_version")
    if (
        schema_version not in {1, 2}
        or index.get("category") != "AI 냠냠"
        or index.get("managed_by") != "ai-namnyam-pilot"
    ):
        errors.append(
            problem(
                "INDEX_SCHEMA_INVALID",
                "Use schema version 1 or 2, category AI 냠냠, and the pilot manager id.",
                "content-index.json",
            )
        )

    hub = index.get("hub")
    if (
        stage in {"prepare", "publish"}
        and (not isinstance(hub, dict) or hub.get("status") != "published" or not hub.get("url"))
    ):
        errors.append(problem("HUB_NOT_PUBLISHED", "Publish the new-series hub before a pilot post.", "content-index.json"))

    posts = index.get("posts")
    if not isinstance(posts, list):
        errors.append(problem("INDEX_SCHEMA_INVALID", "posts must be a list.", "content-index.json"))
        return {"trend": 0, "evergreen": 0, "entry": 0, "proof": 0}

    post_objects = [item for item in posts if isinstance(item, dict)]
    for field in ("post_id", "title"):
        values = [item.get(field) for item in post_objects if item.get(field)]
        if len(values) != len(set(values)):
            errors.append(
                problem(
                    "INDEX_DUPLICATE",
                    f"Every non-empty {field} must be unique.",
                    "content-index.json",
                )
            )
    urls = [item.get("url") for item in post_objects if item.get("url")]
    if len(urls) != len(set(urls)):
        errors.append(
            problem("INDEX_DUPLICATE", "Every published URL must be unique.", "content-index.json")
        )

    by_id = {
        item.get("post_id"): item
        for item in post_objects
        if isinstance(item.get("post_id"), str) and item.get("post_id")
    }

    if schema_version == 2:
        required_v2 = (
            "cluster_id",
            "content_role",
            "recommended_next_id",
            "published_at",
            "facts_checked_at",
            "freshness_due",
            "source_hash",
            "d7_review",
            "d28_review",
            "publishing_state",
        )
        for item in post_objects:
            if any(field not in item for field in required_v2):
                errors.append(
                    problem(
                        "INDEX_V2_FIELD_MISSING",
                        "Every V2 post needs relationship, freshness, review, and publishing fields.",
                        "content-index.json",
                    )
                )
                continue
            legacy = item.get("legacy_excluded") is True or item.get("publishing_state") == "legacy_excluded"
            if legacy:
                continue
            if item.get("content_role") not in CONTENT_ROLES:
                errors.append(
                    problem(
                        "CONTENT_ROLE_INVALID",
                        "Every managed V2 post must use content_role entry or proof.",
                        "content-index.json",
                    )
                )
            if not isinstance(item.get("cluster_id"), str) or not item.get("cluster_id", "").strip():
                errors.append(
                    problem(
                        "INDEX_V2_FIELD_INVALID",
                        "Every managed V2 post needs a non-empty cluster_id.",
                        "content-index.json",
                    )
                )
            publishing_state = item.get("publishing_state")
            if publishing_state not in PUBLISHING_STATES:
                errors.append(
                    problem(
                        "PUBLISHING_STATE_INVALID",
                        "Use a supported publishing_state.",
                        "content-index.json",
                    )
                )
            checked = iso_date(item.get("facts_checked_at"))
            freshness = iso_date(item.get("freshness_due"))
            if checked is None or freshness is None or freshness < checked:
                errors.append(
                    problem(
                        "FRESHNESS_DATE_INVALID",
                        "facts_checked_at and freshness_due must be ordered ISO dates.",
                        "content-index.json",
                    )
                )
            source_hash_required = (
                item.get("publishing_state") == "published"
                or (
                    item.get("post_id") == brief.get("post_id")
                    and stage in {"prepare", "publish"}
                )
            )
            if source_hash_required and (
                not isinstance(item.get("source_hash"), str)
                or not item.get("source_hash", "").strip()
            ):
                errors.append(
                    problem(
                        "SOURCE_HASH_MISSING",
                        "Every managed V2 post needs a source_hash.",
                        "content-index.json",
                    )
                )
            if publishing_state == "published":
                if not item.get("url") or iso_date(item.get("published_at")) is None:
                    errors.append(
                        problem(
                            "PUBLISHED_METADATA_MISSING",
                            "Published posts need a URL and ISO published_at date.",
                            "content-index.json",
                        )
                    )
            next_id = item.get("recommended_next_id")
            if not isinstance(next_id, str):
                errors.append(
                    problem(
                        "NEXT_RELATION_INVALID",
                        "recommended_next_id must be a string.",
                        "content-index.json",
                    )
                )
            elif next_id:
                if next_id == item.get("post_id") or next_id not in by_id:
                    errors.append(
                        problem(
                            "NEXT_RELATION_INVALID",
                            "recommended_next_id must point to another indexed post.",
                            "content-index.json",
                        )
                    )

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
        if schema_version == 2:
            for field in ("cluster_id", "content_role"):
                if item.get(field) != brief.get(field):
                    errors.append(
                        problem(
                            "INDEX_POST_MISMATCH",
                            f"Index {field} does not match brief.md.",
                            "content-index.json",
                        )
                    )
            if item.get("recommended_next_id", "") != draft.get("recommended_next_id", ""):
                errors.append(
                    problem(
                        "NEXT_RELATION_MISMATCH",
                        "Draft and index recommended_next_id values must match.",
                        "content-index.json",
                    )
                )

    if schema_version == 1:
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
    if isinstance(hub, dict) and draft.get("hub_url") != hub.get("url", ""):
        errors.append(problem("HUB_LINK_MISMATCH", "draft hub_url must match the index hub URL.", "draft.md"))

    counts = {"trend": 0, "evergreen": 0, "entry": 0, "proof": 0}
    for item in posts:
        if not isinstance(item, dict) or item.get("legacy_excluded") is True:
            continue
        for field in ("topic_type", "content_role"):
            value = item.get(field)
            if value in counts:
                counts[value] += 1
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
        outline_heading = "제안 목차" if stage == "proposal" else "승인된 목차"
        approved_outline = section_bullets(brief_body, outline_heading)
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
        title_candidates = section_numbered_items(brief_body, "제목 후보")
        if brief.get("selected_title") != draft.get("title"):
            errors.append(
                problem(
                    "SELECTED_TITLE_MISMATCH",
                    "brief selected_title must equal the draft title.",
                    "draft.md",
                )
            )
        if draft.get("title") not in title_candidates:
            errors.append(
                problem(
                    "TITLE_NOT_IN_CANDIDATES",
                    "The draft title must be one of the three title candidates.",
                    "draft.md",
                )
            )
        brief_sources: list[str] = []
        for value in (brief.get("primary_sources", []), brief.get("independent_sources", [])):
            if isinstance(value, list):
                brief_sources.extend(item for item in value if isinstance(item, str))
        draft_source_list = draft.get("sources", [])
        if isinstance(draft_source_list, list) and sorted(brief_sources) != sorted(draft_source_list):
            errors.append(
                problem(
                    "SOURCE_LIST_MISMATCH",
                    "Draft sources must match the brief source lists.",
                    "draft.md",
                )
            )
        v2_mode = any(field in brief for field in BRIEF_V2_FIELDS)
        if v2_mode:
            for field in validate_draft.PILOT_V2_FIELDS:
                if field not in draft:
                    errors.append(
                        problem(
                            "DRAFT_V2_FIELD_MISSING",
                            f"Missing V2 draft field: {field}",
                            "draft.md",
                        )
                    )
            for field in ("one_line_answer", "facts_checked_at"):
                if brief.get(field) != draft.get(field):
                    errors.append(
                        problem(
                            "BRIEF_DRAFT_MISMATCH",
                            f"{field} differs between files.",
                            "draft.md",
                        )
                    )

            captured_at = iso_date(draft.get("evidence_captured_at"))
            if captured_at is None:
                errors.append(
                    problem(
                        "MEDIA_METADATA_INVALID",
                        "evidence_captured_at must use YYYY-MM-DD.",
                        "draft.md",
                    )
                )
            source = draft.get("evidence_source")
            if not isinstance(source, str) or not source.strip():
                errors.append(
                    problem(
                        "MEDIA_METADATA_INVALID",
                        "evidence_source must identify the owner or source URL.",
                        "draft.md",
                    )
                )
            use_basis = draft.get("evidence_use_basis")
            if not isinstance(use_basis, str) or not use_basis.strip():
                errors.append(
                    problem(
                        "MEDIA_METADATA_INVALID",
                        "evidence_use_basis must explain why the image may be used.",
                        "draft.md",
                    )
                )
        for field in ("cover_image", "evidence_image"):
            value = draft.get(field, "")
            image_path = (post_dir / value).resolve() if isinstance(value, str) else post_dir
            try:
                image_path.relative_to(post_dir.resolve())
            except ValueError:
                errors.append(problem("MEDIA_PATH_INVALID", f"{field} must stay inside the post folder.", "draft.md"))
            else:
                if not image_path.is_file():
                    errors.append(problem("MEDIA_FILE_MISSING", f"Missing file for {field}.", "draft.md"))
                elif image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                    errors.append(
                        problem(
                            "MEDIA_TYPE_INVALID",
                            f"{field} must use PNG, JPEG, GIF, or WebP.",
                            "draft.md",
                        )
                    )
                elif image_path.stat().st_size == 0:
                    errors.append(
                        problem("MEDIA_FILE_EMPTY", f"{field} cannot be empty.", "draft.md")
                    )
        if stage == "proposal" and draft.get("status") != "proposal":
            errors.append(problem("DRAFT_NOT_PROPOSAL", "Proposal validation requires status proposal.", "draft.md"))
        if stage == "prepare" and draft.get("status") not in {"draft", "final-approved"}:
            errors.append(problem("DRAFT_NOT_READY", "Prepare requires an approved draft status.", "draft.md"))
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
    mix = (
        validate_index(index, brief, draft, stage, errors)
        if index and brief and draft
        else {"trend": 0, "evergreen": 0, "entry": 0, "proof": 0}
    )
    if index.get("schema_version") == 1 and mix["trend"] + mix["evergreen"] == 8 and (
        mix["trend"] != 6 or mix["evergreen"] != 2
    ):
        warnings.append(
            problem(
                "PILOT_MIX_DEVIATION",
                "The eight-post pilot differs from the six trend / two evergreen target.",
                "content-index.json",
            )
        )
    if index.get("schema_version") == 2 and mix["entry"] + mix["proof"] == 8 and (
        mix["entry"] != 4 or mix["proof"] != 4
    ):
        warnings.append(
            problem(
                "PILOT_PAIR_DEVIATION",
                "The eight-post pilot should contain four entry and four proof posts.",
                "content-index.json",
            )
        )

    if index.get("schema_version") == 2 and draft and draft_text:
        next_id = draft.get("recommended_next_id", "")
        posts = index.get("posts", [])
        target = next(
            (
                item
                for item in posts
                if isinstance(item, dict) and item.get("post_id") == next_id
            ),
            None,
        )
        if target and target.get("publishing_state") == "published":
            target_url = target.get("url", "")
            link_label = draft.get("recommended_next_label", "")
            if (
                not target_url
                or target_url not in draft_text
                or not link_label
                or link_label not in draft_text
            ):
                errors.append(
                    problem(
                        "NEXT_LINK_MISSING_BODY",
                        "A published recommended next post needs its URL and descriptive label in the body.",
                        "draft.md",
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
            "entry_posts": mix["entry"],
            "proof_posts": mix["proof"],
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
    parser.add_argument("--stage", choices=("proposal", "prepare", "publish"), default="prepare")
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
