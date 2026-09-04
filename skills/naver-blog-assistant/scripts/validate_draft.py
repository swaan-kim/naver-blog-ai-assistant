#!/usr/bin/env python3
"""Validate a Naver Blog Markdown draft without echoing its body.

The accepted frontmatter is intentionally small and dependency-free: top-level
scalars plus block or inline lists are enough for the bundled draft template.
Exit status is 0 for a valid draft, 1 for validation failures, and 2 for an
unreadable file or invalid command-line options.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MIN_CHARS = 1_800
DEFAULT_MAX_CHARS = 2_200
DEFAULT_MIN_HEADINGS = 4
DEFAULT_MAX_HEADINGS = 6
MAX_REPORTED_PROBLEMS = 12
MAX_SUMMARY_TITLE_CHARS = 120
REQUIRED_FIELDS = ("title", "category", "tags", "images")
HANGUL_RE = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+\S")


@dataclass(frozen=True)
class Problem:
    code: str
    message: str
    line: int | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message[:240]}
        if self.line is not None:
            result["line"] = self.line
        return result


class FrontmatterError(ValueError):
    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.line = line


def _make_result(
    summary: dict[str, Any], errors: list[Problem], warnings: list[Problem]
) -> dict[str, Any]:
    """Bound user-controlled output while retaining total problem counts."""
    safe_summary = dict(summary)
    title = safe_summary.get("title", "")
    if isinstance(title, str) and len(title) > MAX_SUMMARY_TITLE_CHARS:
        safe_summary["title"] = title[:MAX_SUMMARY_TITLE_CHARS]
        safe_summary["title_truncated"] = True
    safe_summary["error_count"] = len(errors)
    safe_summary["warning_count"] = len(warnings)

    def compact(problems: list[Problem]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], list[Problem]] = {}
        for problem in problems:
            grouped.setdefault((problem.code, problem.message), []).append(problem)
        rendered: list[dict[str, Any]] = []
        for group in list(grouped.values())[:MAX_REPORTED_PROBLEMS]:
            item = group[0].as_dict()
            if len(group) > 1:
                item["count"] = len(group)
            rendered.append(item)
        return rendered

    return {
        "ok": not errors,
        "summary": safe_summary,
        "errors": compact(errors),
        "warnings": compact(warnings),
    }


def _unquote(value: str, line: int | None = None) -> str:
    value = value.strip()
    begins_quoted = value.startswith(('"', "'"))
    ends_quoted = value.endswith(('"', "'"))
    if begins_quoted and (not ends_quoted or value[0] != value[-1]):
        raise FrontmatterError("Unbalanced quoted value.", line)
    if len(value) >= 2 and begins_quoted:
        if value[0] == '"':
            try:
                decoded = json.loads(value)
                if isinstance(decoded, str):
                    return decoded
            except json.JSONDecodeError as exc:
                raise FrontmatterError("Invalid double-quoted value.", line) from exc
        return value[1:-1].replace("''", "'")
    return value


def _parse_inline_list(value: str, line: int) -> list[str]:
    if not (value.startswith("[") and value.endswith("]")):
        raise FrontmatterError("Inline lists must end with ']'.", line)
    inner = value[1:-1].strip()
    if not inner:
        return []

    parts: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    escaped = False
    for character in inner:
        if escaped:
            buffer.append(character)
            escaped = False
            continue
        if quote == '"' and character == "\\":
            buffer.append(character)
            escaped = True
            continue
        if character in {'"', "'"}:
            if quote is None and not "".join(buffer).strip():
                quote = character
            elif quote == character:
                quote = None
            buffer.append(character)
            continue
        if character == "," and quote is None:
            parts.append("".join(buffer).strip())
            buffer = []
            continue
        buffer.append(character)
    if quote is not None or escaped:
        raise FrontmatterError("Unbalanced quote in inline list.", line)
    parts.append("".join(buffer).strip())
    if any(not part for part in parts):
        raise FrontmatterError("Inline lists cannot contain empty items.", line)
    return [_unquote(item, line) for item in parts]


def parse_document(text: str) -> tuple[dict[str, Any], list[str], int]:
    """Return metadata, body lines, and the body start line (one-based)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("The file must start with YAML frontmatter ('---').", 1)

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        raise FrontmatterError("The YAML frontmatter has no closing '---'.", 1)

    metadata: dict[str, Any] = {}
    pending_list: str | None = None
    for index in range(1, closing_index):
        source = lines[index]
        line_number = index + 1
        stripped = source.strip()
        if not stripped or stripped.startswith("#"):
            continue

        item_match = re.match(r"^\s*-\s*(.*)$", source)
        if item_match is not None:
            if pending_list is None:
                raise FrontmatterError("A list item must follow an empty list field.", line_number)
            metadata[pending_list].append(_unquote(item_match.group(1), line_number))
            continue

        if source[:1].isspace():
            if pending_list is None:
                raise FrontmatterError("Only indented list items are supported here.", line_number)
            raise FrontmatterError("Expected a '-' list item.", line_number)

        key_match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$", source)
        if key_match is None:
            raise FrontmatterError("Expected a top-level 'key: value' entry.", line_number)
        key, raw_value = key_match.group(1), (key_match.group(2) or "").strip()
        if key in metadata:
            raise FrontmatterError(f"Duplicate frontmatter key: {key}", line_number)

        pending_list = None
        if raw_value == "":
            metadata[key] = []
            pending_list = key
        elif raw_value.startswith("["):
            metadata[key] = _parse_inline_list(raw_value, line_number)
        else:
            metadata[key] = _unquote(raw_value, line_number)

    return metadata, lines[closing_index + 1 :], closing_index + 2


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()


def _visible_line(line: str) -> str:
    value = line
    previous = None
    while value != previous:
        previous = value
        value = re.sub(r"^\s*>\s?", "", value)
        value = re.sub(r"^\s{0,3}#{1,6}\s+", "", value)
        value = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", value)
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_~`]", "", value)
    if "|" in value:
        value = value.replace("|", " ")
    return value.strip()


def _is_table_divider(line: str) -> bool:
    stripped = line.strip().strip("|").strip()
    if "|" not in stripped:
        return False
    cells = [cell.strip() for cell in stripped.split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _visible_body(body_lines: list[str]) -> str:
    visible: list[str] = []
    in_fence = False
    for line in body_lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and _is_table_divider(line):
            continue
        value = line.strip() if in_fence else _visible_line(line)
        if value:
            visible.append(value)
    return re.sub(r"\s+", " ", " ".join(visible)).strip()


def _line_kind(line: str, in_fence: bool) -> str:
    stripped = line.strip()
    if stripped.startswith("```"):
        return "fence"
    if in_fence:
        return "code"
    if not stripped:
        return "blank"
    if HEADING_RE.match(line):
        return "heading"
    if LIST_RE.match(line):
        return "list"
    if stripped.startswith((">", "![")) or "|" in stripped or _is_table_divider(line):
        return "structure"
    return "prose"


def _layout_metrics_and_problems(
    body_lines: list[str], body_start_line: int
) -> tuple[int, int, list[Problem]]:
    kinds: list[str] = []
    in_fence = False
    fence_start_line: int | None = None
    for line in body_lines:
        kind = _line_kind(line, in_fence)
        kinds.append(kind)
        if kind == "fence":
            if not in_fence:
                fence_start_line = body_start_line + len(kinds) - 1
            in_fence = not in_fence
            if not in_fence:
                fence_start_line = None

    problems: list[Problem] = []
    if in_fence:
        problems.append(
            Problem(
                "MARKDOWN_FENCE_UNCLOSED",
                "Close the fenced code block before the end of the draft.",
                fence_start_line,
            )
        )
    heading_count = 0
    for index, kind in enumerate(kinds):
        if kind != "heading":
            continue
        heading_count += 1
        actual_line = body_start_line + index
        if index == 0 or kinds[index - 1] != "blank":
            problems.append(
                Problem(
                    "HEADING_SPACE_BEFORE",
                    "Leave one blank line before each heading.",
                    actual_line,
                )
            )
        if index == len(kinds) - 1 or kinds[index + 1] != "blank":
            problems.append(
                Problem(
                    "HEADING_SPACE_AFTER",
                    "Leave one blank line after each heading.",
                    actual_line,
                )
            )

    for index in range(1, len(kinds)):
        if kinds[index - 1] == kinds[index] == "prose":
            problems.append(
                Problem(
                    "PARAGRAPH_SPACING",
                    "Separate prose paragraphs with a blank line; keep each draft paragraph on one line.",
                    body_start_line + index,
                )
            )

    paragraph_count = 0
    previous_kind = "blank"
    for kind in kinds:
        if kind == "prose" and previous_kind != "prose":
            paragraph_count += 1
        previous_kind = kind
    return heading_count, paragraph_count, problems


def validate_text(
    text: str,
    *,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_headings: int = DEFAULT_MIN_HEADINGS,
    max_headings: int = DEFAULT_MAX_HEADINGS,
) -> dict[str, Any]:
    errors: list[Problem] = []
    warnings: list[Problem] = []
    metadata: dict[str, Any] = {}
    body_lines: list[str] = []
    body_start_line = 1

    try:
        metadata, body_lines, body_start_line = parse_document(text)
    except FrontmatterError as exc:
        errors.append(Problem("FRONTMATTER_INVALID", str(exc), exc.line))
        return _make_result(
            {
                "title": "",
                "body_chars": 0,
                "hangul_chars": 0,
                "headings": 0,
                "paragraphs": 0,
                "tags": 0,
                "images": 0,
                "sources": 0,
                "title_in_body": 0,
            },
            errors,
            warnings,
        )

    for field in REQUIRED_FIELDS:
        if field not in metadata:
            errors.append(Problem("FIELD_MISSING", f"Required frontmatter field is missing: {field}"))

    title = metadata.get("title", "")
    category = metadata.get("category", "")
    tags = metadata.get("tags", [])
    images = metadata.get("images", [])

    for field, value in (("title", title), ("category", category)):
        if field in metadata and (not isinstance(value, str) or not value.strip()):
            errors.append(Problem("FIELD_INVALID", f"{field} must be a non-empty string."))
    sources = metadata.get("sources", [])
    for field, value in (("tags", tags), ("images", images), ("sources", sources)):
        if field in metadata and (
            not isinstance(value, list)
            or any(not isinstance(item, str) or not item.strip() for item in value)
        ):
            errors.append(Problem("FIELD_INVALID", f"{field} must be a list of non-empty strings."))

    duplicate_tags: list[str] = []
    if isinstance(tags, list):
        seen_tags: set[str] = set()
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                continue
            normalized = _normalize(tag.lstrip("#"))
            if normalized in seen_tags and normalized not in duplicate_tags:
                duplicate_tags.append(normalized)
            seen_tags.add(normalized)
    if duplicate_tags:
        errors.append(Problem("TAG_DUPLICATE", "Remove duplicate tags."))

    visible_body = _visible_body(body_lines)
    body_chars = len(visible_body)
    hangul_chars = len(HANGUL_RE.findall(visible_body))
    if not visible_body:
        errors.append(Problem("BODY_EMPTY", "The Markdown body is empty."))
    elif hangul_chars == 0:
        errors.append(Problem("BODY_NO_HANGUL", "The body must contain Korean text."))
    if body_chars < min_chars:
        errors.append(
            Problem("BODY_TOO_SHORT", f"Body has {body_chars} characters; minimum is {min_chars}.")
        )
    elif body_chars > max_chars:
        errors.append(
            Problem("BODY_TOO_LONG", f"Body has {body_chars} characters; maximum is {max_chars}.")
        )

    title_in_body_count = 0
    if isinstance(title, str) and title.strip():
        normalized_title = _normalize(title)
        in_fence = False
        for line in body_lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence and _normalize(_visible_line(line)) == normalized_title:
                title_in_body_count += 1
        if title_in_body_count:
            errors.append(
                Problem(
                    "TITLE_DUPLICATED_IN_BODY",
                    "The post title also appears as a standalone body line.",
                )
            )

    heading_count, paragraph_count, layout_problems = _layout_metrics_and_problems(
        body_lines, body_start_line
    )
    errors.extend(layout_problems)
    if heading_count < min_headings:
        errors.append(
            Problem(
                "HEADINGS_TOO_FEW",
                f"Body has {heading_count} headings; minimum is {min_headings}.",
            )
        )
    elif heading_count > max_headings:
        errors.append(
            Problem(
                "HEADINGS_TOO_MANY",
                f"Body has {heading_count} headings; maximum is {max_headings}.",
            )
        )
    if heading_count == 0:
        warnings.append(Problem("HEADING_MISSING", "The body has no Markdown headings."))

    return _make_result(
        {
            "title": title if isinstance(title, str) else "",
            "body_chars": body_chars,
            "hangul_chars": hangul_chars,
            "headings": heading_count,
            "paragraphs": paragraph_count,
            "tags": len(tags) if isinstance(tags, list) else 0,
            "images": len(images) if isinstance(images, list) else 0,
            "sources": len(sources) if isinstance(sources, list) else 0,
            "title_in_body": title_in_body_count,
        },
        errors,
        warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, help="UTF-8 Markdown draft to validate")
    parser.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--min-headings", type=int, default=DEFAULT_MIN_HEADINGS)
    parser.add_argument("--max-headings", type=int, default=DEFAULT_MAX_HEADINGS)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Compatibility flag; compact JSON is already the default output.",
    )
    parser.add_argument("--pretty", action="store_true", help="Indent JSON for local debugging")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    if (
        args.min_chars < 0
        or args.max_chars < args.min_chars
        or args.min_headings < 0
        or args.max_headings < args.min_headings
    ):
        print(
            json.dumps(
                {"ok": False, "error": "INVALID_LIMITS"},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 2
    try:
        text = args.draft.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        print(
            json.dumps(
                {"ok": False, "error": "DRAFT_UNREADABLE"},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 2

    result = validate_text(
        text,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
        min_headings=args.min_headings,
        max_headings=args.max_headings,
    )
    indent = 2 if args.pretty else None
    separators = None if args.pretty else (",", ":")
    print(json.dumps(result, ensure_ascii=False, indent=indent, separators=separators))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
