# Naver editor workflow

Read only for editor preparation or publication.

## Boundary

- The owner signs in. Never inspect credentials, codes, cookies, or session storage.
- Always open a new post; never change the nine legacy posts or an unrelated draft.
- Prepare from the local `draft.md` path. Do not relay its body through the model.
- Read `../assets/review-checklist.md`; scripts handle structural checks.
- Require `AI_NAMNYAM_PILOT_ROOT`; draft, shared index, and all media must resolve inside it without symlink escapes.
- If an expected locator is missing, stop with `SELECTOR_MISS`; never guess coordinates.
- Keep sessions and diagnostics out of Git. Return no DOM or screenshot on success.
- The Playwright/MCP engine is external. Do not claim it is bundled before testing.

## Prepare

1. Run package validation at stage `prepare`.
2. Enter title, first-screen block, internal TOC, body, category `AI 냠냠`, unique tags, cover, evidence image, and requested formatting in batches.
3. Set and verify the Naver AI-use checkbox for both `true` and `false`; never inherit a prior post's state.
4. Verify only title, section order, category, images, links, and unresolved-marker count.
5. Stop in the editor for owner review. Do not click publish.

## Publish transaction

Proceed only when the owner sends exactly `발행` for the current post. Run stage `publish`, confirm the expected title, then persist `publishing` with the source hash before the irreversible click.

Accept only an owned `https://blog.naver.com` result with numeric `logNo`. On success, record `published`. If the process stops after the click or the result cannot be reconciled, persist `outcome_uncertain` and block all automatic retries until the owner checks Naver and repairs the index.

After success, use `distribution-linking.md` to update the hub and named semantic relation. Never choose by chronology or edit legacy posts. On failure report `PARTIAL_LINK_UPDATE`; do not republish.

The first new-series post needs the hub link but may have no next link until its target exists. A coordinate fallback is never allowed. Stored role, label, and selector locators plus a UI fingerprint provide the token-saving normal path.
