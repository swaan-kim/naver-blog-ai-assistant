# Safe Naver editor workflow

Read this file only when the user asks to enter or format a draft in Naver Blog.

## Safety boundary

- Let the user sign in directly.
- Never request or inspect passwords, one-time codes, cookies, or browser session storage.
- Do not modify or delete existing posts or saved drafts.
- Never press the final publication button. Stop at the publication settings screen.
- Treat unexpected dialogs, editor changes, or ambiguous draft state as a reason to pause.

## Editor procedure

1. Inspect the visible page and confirm that it is Naver Blog's editor.
2. Check whether an existing draft or recovery dialog is present.
3. Preserve the existing content. Open a separate new editor for the requested post.
4. Enter the title once in the title field.
5. Enter the body without duplicating the title.
6. Apply the requested font, size, alignment, line spacing, heading emphasis, blank paragraphs, and flow indentation.
7. Set the requested category and tags.
8. Validate the editor state before saving.
9. Save as a draft.
10. Open publication settings, verify the category and tags, and stop for user approval.

## Validation gate

Require all checks to pass before moving to publication settings:

- the title appears exactly once in the title area;
- every planned paragraph appears once and in order;
- the body length is within the agreed range or the deviation is disclosed;
- every heading has a visible separation from the preceding section;
- the process flow or callout is visually distinct when requested;
- the category matches the request;
- tags contain no duplicates;
- the draft save state is visible;
- no existing post or draft was overwritten.

If the editor exposes placeholder text such as a quotation source prompt, distinguish the placeholder from saved article content before reporting it as an error.

## Handoff wording

State that the draft has been saved and the publication settings are open. List the validated category and tags, then tell the user that the final publication button is ready for their direct approval.
