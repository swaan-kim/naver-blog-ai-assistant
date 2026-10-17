# AI 냠냠 editorial workflow

Read for topic selection, outline approval, and pilot operation.

## Weekly invocation

When the owner says `이번 주 AI 냠냠 시작`, research and return five compact candidates. Do not draft yet.

For each candidate show only:

- reader question and `trend` or `evergreen`;
- why now;
- meaning for a nondeveloper office worker;
- evidence level and primary source date;
- follow-up verification method;
- overlap with existing posts.

Search current announcements from the previous 14 days and the evergreen question backlog. Use recent official announcements, papers, or public-agency material as core evidence. Media and newsletters may provide context or discovery. Social posts and rumors cannot stand alone.

Aim for six `trend` and two `evergreen` posts across the eight-post pilot (the operating target is 70/30, not a promise that every five-candidate set has an exact ratio). Check `content-index.json` before proposing topics.

For medical, legal, financial, or political topics, require both an official and a reliable independent source. Offer explanation only, never personalized advice.

## Gates and artifacts

1. Owner chooses a candidate: mark `topic_status: approved` in `brief.md`.
2. Propose three titles and an outline. Draft only after `outline_status: approved`.
3. For `직접 써봤습니다`, capture four owner notes in conversation: intended job, convenience, friction, and reuse decision. Do not turn them into a questionnaire.
4. Create `draft.md` once, then patch sections only.
5. After editor review, mark `final_status: approved` only on explicit approval.
6. The exact current-task command `발행` is the final runtime authorization; never infer it from a file status.

Keep only `brief.md`, `draft.md`, and the shared `content-index.json`. Do not store source-page dumps or Naver DOM. Use `assets/brief-template.md`, `assets/draft-template.md`, and `assets/content-index-template.json`.

If the same edit request recurs three times, propose one rule; add it only after the owner approves. Do not update the public skill or README until eight pilot posts meet the agreed completion criteria.
