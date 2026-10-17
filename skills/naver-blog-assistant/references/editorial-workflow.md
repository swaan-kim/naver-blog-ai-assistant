# AI 냠냠 editorial workflow

## Weekly invocation

When the owner says `이번 주 AI 냠냠 시작`, research and return five compact candidates. Do not draft yet.

For each show only: reader question; `trend` or `evergreen`; why now; office-worker meaning; evidence/date; follow-up check; existing-post overlap.

Use the five-point discussion scorecard in `pilot/START-HERE.md` when the pilot workspace is present. It prioritizes topics; it never predicts traffic.

Search the previous 14 days and the evergreen backlog. Core evidence must be an official announcement, paper, or public-agency source. Media may add context; rumors cannot stand alone.

Across eight posts aim for six `trend` and two `evergreen`; this is the nearest whole-post mix to 70/30. Check `content-index.json` first.

Medical, legal, financial, or political topics need official and reliable independent sources. Explain only; never give personal advice.

## Gates and artifacts

1. Owner chooses a candidate; mark `topic_status: approved`.
2. Propose three titles and an outline. Draft only after `outline_status: approved`.
3. For `직접 써봤습니다`, capture the owner's goal, convenience, friction, and reuse decision in conversation.
4. Create `draft.md` once, then patch sections only.
5. Mark `final_status: approved` only on explicit approval.
6. Only the exact current-task command `발행` authorizes publication.

Keep only `brief.md`, `draft.md`, and shared `content-index.json`; never store source dumps or Naver DOM.

Before drafting, fill `primary_query`, `reader_reward`, `owner_angle`, `next_link_plan`, and `selected_title` in `brief.md`. Require one concrete scene, one limit, and one reusable action.

Requested samples stay `proposal` with pending approvals and blank `hub_url`; validate with `--stage proposal`. After approval, rename `제안 목차` to `승인된 목차`, add the hub URL, and change to `draft`. Proposals must fail `--stage prepare`.

After an edit repeats three times, propose one rule and add it only if approved. Keep the public skill unchanged until the eight-post pilot passes.
