# Naver editor workflow

Read only for Naver entry or publication.

## Boundary

- The user signs in; never inspect credentials, codes, cookies, or session storage.
- Always create a new post and preserve existing posts and drafts.
- Default to review mode. Publish only on an explicit current-task request.
- On an ambiguous page or target, stop with `EDITOR_STATE_MISMATCH`; never guess a new coordinate.
- Keep sessions and diagnostics out of Git.

## Efficient path

1. Validate the draft file before opening Naver.
2. Prefer one file-path call such as `prepare_post(draft_path)` when available.
3. Otherwise inspect the editor once, use labels, roles, or stable selectors, and enter title/body in batches. A documented coordinate is fallback only.
4. Apply the requested category, tags, font, spacing, heading emphasis, and indentation.
5. Verify required fields only. Do not retrieve both a full DOM and screenshot or return either on success.
6. Stop for review. If publication was explicitly requested, recheck the gate and publish once.

Never re-send the article body between steps. On failure, save one relevant screenshot, HTML fragment, or trace locally; return only the failed stage and path.

## Gate

- exact title in its field; no duplicate title in the body;
- planned headings and paragraphs in order;
- length deviation disclosed;
- visible heading spacing and nested step indentation;
- requested category and unique tags;
- no overwritten content;
- explicit user intent before publication.
