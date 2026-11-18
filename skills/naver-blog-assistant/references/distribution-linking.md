# Hub and semantic linking

Read only when creating or updating the new-series hub or related links.

## Boundary

- Manage only `AI 냠냠` posts recorded in the v2 index.
- Existing nine posts are `legacy_excluded`; never edit or add them to the new hub.
- Use `cluster_id`, `content_role`, and `recommended_next_id`. Do not infer the next article from publication order.
- A published post gets at most two navigation links: the hub and one meaningful next post.

## Hub

Title: `AI를 일에 써보고 싶은 사람의 시작 지도`.

Group posts by reader problem, not by editorial format:

1. 반복 업무를 줄이는 AI
2. 개발자를 기다리지 않고 직접 해보기
3. 회사에서 안전하게 AI 쓰기
4. AI 결과를 덜 어색하게 다듬기

Formats such as `3분 AI 정리` and `직접 써봤습니다` appear only as small labels.

## Link labels

Never use only `이전 글`, `다음 글`, or `더 보기`. The visible label must say what the reader will gain, for example `AI가 정리한 회의록을 실제 할 일로 바꾸는 방법`.

An `entry` post normally points to the `proof` post in the same cluster. A `proof` post may point to the next best question when that target already exists; otherwise keep the ID and label in the index but do not render a broken link.

## Transaction

After verified publication:

1. store the owned Naver URL and `published_at`;
2. update the index state to `published`;
3. add the post once to its hub section;
4. update only the explicitly related new-series article;
5. verify both owned URLs.

If a link update fails, keep the new post and report `PARTIAL_LINK_UPDATE`. Never republish it. If the publication outcome is uncertain, keep `outcome_uncertain` and perform no automatic link edits until the owner reconciles Naver and the index.
