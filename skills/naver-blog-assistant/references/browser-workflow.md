# Naver editor workflow

Read only for editor preparation or publication.

## Boundary

- The owner signs in. Never inspect credentials, codes, cookies, or session storage.
- Always open a new post; never change the nine legacy posts or an unrelated draft.
- Prepare from the local `draft.md` path. Do not relay its body through the model.
- If an expected locator is missing, stop with `SELECTOR_MISS`; never guess coordinates.
- Keep sessions and diagnostics out of Git. Return no DOM or screenshot on success.

## Prepare

1. Run package validation at stage `prepare`.
2. Enter title, body, category `AI 냠냠`, unique tags, cover, evidence image, and requested formatting in batches.
3. Apply the Naver AI-use setting when `ai_media` is true.
4. Verify only title, section order, category, images, links, and unresolved-marker count.
5. Stop in the editor for owner review. Do not click publish.

## Publish transaction

Proceed only when the owner sends exactly `발행` for the current post. Run stage `publish`, confirm the expected title, then publish once.

After a successful post, update the new-series hub and the previous new-system post's next link. Never edit legacy posts. If either link update fails, report `PARTIAL_LINK_UPDATE` with the published URL; do not publish a duplicate.

The first new-series post needs the hub link but may have no previous or paired link. A coordinate fallback is never allowed for publication or destructive edits.
