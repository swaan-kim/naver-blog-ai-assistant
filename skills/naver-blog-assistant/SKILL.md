---
name: naver-blog-assistant
description: Plan, write, validate, or prepare AI 냠냠 Naver posts. Use for topic candidates, owner-voice drafts, file-first revisions, pilot checks, and safe editor preparation. Never handle credentials or publish without the user's exact command.
---

# AI 냠냠 Naver Blog Assistant

솜솜 works internally; public copy uses the owner's voice.

## Route

- Topics or trends: [topic-research.md](references/topic-research.md)
- Approval and planning: [editorial-workflow.md](references/editorial-workflow.md)
- Draft or revision: [writing-guide.md](references/writing-guide.md)
- Naver prepare/publish: [browser-workflow.md](references/browser-workflow.md)
- Hub and next links: [distribution-linking.md](references/distribution-linking.md)
- Metrics and review: [measurement-guide.md](references/measurement-guide.md)

Resources: `assets/draft-template.md`, `assets/article-request.yaml`, `assets/persona-template.md`, `scripts/validate_draft.py`, `scripts/validate_package.py`. Resolve paths here; never replace a missing mascot.

## File-first flow

1. Draft only after topic and outline approval.
2. Create `brief.md`, `draft.md`; update v2 `content-index.json`.
3. Generate once; patch only named sections.
4. Validate samples with `--stage proposal`, approved work with `--stage prepare`.
5. Prepare a new editor and stop for review. The editor engine is external.
6. Publish only after exact `발행` and `--stage publish` validation.

Do not echo the draft, DOM, screenshot, or trace. Return compact status.

Exclude legacy posts. Link by problem cluster and semantic next post, never chronology alone.
