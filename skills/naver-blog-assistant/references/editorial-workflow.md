# AI 냠냠 editorial workflow

Read after a topic is selected. Candidate discovery belongs in `topic-research.md`.

The owner approves the topic, outline, and final copy. 솜솜 organizes evidence and edits; the owner remains the only public narrator.

## Gates and artifacts

1. Owner chooses a candidate; mark `topic_status: approved`. Record its `cluster_id` and `content_role`.
2. Propose three titles and an outline. Draft only after `outline_status: approved`.
3. For `직접 써봤습니다`, capture the owner's goal, convenience, friction, and reuse decision in conversation.
4. Create `draft.md` once, then patch sections only.
5. Mark `final_status: approved` only on explicit approval.
6. Only the exact current-task command `발행` authorizes publication.

Keep only `brief.md`, `draft.md`, and shared `content-index.json` per post. A shared `performance-log.csv` may store compact D+7/D+28 metrics. Never store source dumps or Naver DOM.

Before drafting, fill `reader_role`, `reader_problem`, `primary_query`, `one_line_answer`, `unique_proof`, `facts_checked_at`, `publish_by`, and `selected_title`. Record every material claim as `claim|source-url|checked-date|limitation`; the URL must also appear under primary or independent sources.

Require one concrete scene, one limit, one reusable action, and one visible proof. If the proof cannot be produced, change the format to sourced analysis rather than pretending it was used.

Requested samples stay `proposal` with pending approvals and blank `hub_url`; validate with `--stage proposal`. After approval, rename `제안 목차` to `승인된 목차`, add the hub URL, and change to `draft`. Proposals must fail `--stage prepare`.

At publish preparation, recheck whether `publish_by` has passed and whether plan, price, availability, or policy claims changed. After an edit repeats three times, propose one rule and add it only if approved. Keep the public skill unchanged until the eight-post pilot passes.
