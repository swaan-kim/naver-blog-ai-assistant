# 솜솜 · Naver Blog AI Assistant

**긴 원고는 파일에 한 번만 쓰고, 검증과 네이버 준비는 짧게 반복하는 Codex 스킬입니다.**

솜솜은 AI·AX를 비개발자도 읽기 쉽게 설명합니다. 짧은 문단, 넉넉한 목차 간격, 단계별 설명을 기본으로 사용하며 기존 글과 임시저장 글은 건드리지 않습니다.

## 무엇이 달라졌나요?

- 원고 전문을 채팅과 브라우저 사이에서 반복하지 않습니다.
- 작은 피드백은 해당 문단만 고칩니다.
- 글자 수, 제목 중복, 소제목 수, 태그 중복은 로컬 스크립트가 검사합니다.
- 글쓰기 때는 글쓰기 규칙만, 네이버 입력 때는 브라우저 규칙만 읽습니다.
- 작업별 실행 지침은 4,000자 이하인지 자동 테스트합니다.
- 성공 결과는 제목·글자 수·상태만 돌려줍니다.

첫 원고 작성에는 여전히 모델 토큰이 필요합니다. 절감되는 부분은 **원고 재전송, 통째 재작성, 불필요한 화면·DOM 왕복**입니다. 정확한 절감률은 사용 환경에 따라 달라 고정 수치로 약속하지 않습니다.

## 1분 설치

1. **Code → Download ZIP**을 누르거나 [ZIP을 바로 내려받습니다](https://github.com/swaan-kim/naver-blog-ai-assistant/archive/refs/heads/main.zip).
2. ZIP을 풀고 `skills/naver-blog-assistant` 폴더를 복사합니다.
3. 아래 위치에 `naver-blog-assistant`라는 이름으로 붙여 넣습니다.

```text
Windows: C:\Users\사용자이름\.codex\skills\naver-blog-assistant
macOS/Linux: ~/.codex/skills/naver-blog-assistant
```

4. Codex에서 새 작업을 열고 아래 요청문을 사용합니다.

> 글 작성만 할 때는 브라우저 도구가 필요 없습니다. 네이버 자동 입력에는 사용하는 Codex 환경의 브라우저 제어 기능이 필요합니다.

## 바로 쓰는 요청문

### 1. 원고 만들기

```text
$naver-blog-assistant로 ‘AI 에이전트와 챗봇의 차이’를
비개발자용 솜솜 말투로 작성해줘.
내 네이버 카테고리를 모르면 원고를 쓰기 전에 물어봐.
원고는 drafts/ai-agent-vs-chatbot.md에 한 번만 저장하고 검증해줘.
채팅에는 본문을 반복하지 말고 경로와 검증 결과만 알려줘.
```

### 2. 한 부분만 고치기

```text
drafts/ai-agent-vs-chatbot.md의 ‘실제로는 이렇게 움직여요’ 부분만
더 짧고 단계적으로 고쳐줘. 다른 문단은 바꾸지 말고 다시 검증해줘.
```

### 3. 네이버에 준비하기

```text
검증된 drafts/ai-agent-vs-chatbot.md를 읽어
기존 글을 건드리지 말고 네이버 새 편집기에 넣어줘.
목차 앞뒤 간격과 목록 들여쓰기를 적용하고 검수 화면에서 멈춰줘.
```

바로 발행하려면 마지막 문장을 `검증을 통과하면 발행해줘`로 명시해야 합니다. 명시하지 않으면 검수 모드가 기본입니다.

## 입력표를 쓰면 더 안정적입니다

[article-request.yaml](skills/naver-blog-assistant/assets/article-request.yaml)에서 먼저 여섯 가지 콘텐츠 입력을 채웁니다. 네이버에 넣을 때는 계정에 실제로 존재하는 카테고리 이름도 필요합니다.

1. 설명할 개념이나 도구
2. 독자가 겪는 문제
3. 한 문장 결론
4. 직접 확인한 사실과 환경
5. 공식 문서·1차 자료·직접 실험
6. 사람이 판단할 지점

완성 원고는 YAML 머리말이 있는 Markdown 파일입니다.

```yaml
---
title: "글 제목"
category: "내 네이버 카테고리"
tags: ["AI잡학냠냠", "AI조수", "AI기초"]
images: []
sources: []
---
```

나만의 조수를 만들려면 [persona-template.md](skills/naver-blog-assistant/assets/persona-template.md)를 채워 함께 전달하세요.

## 로컬 검증

보통은 솜솜이 자동으로 실행하므로 명령어를 입력할 필요가 없습니다. 직접 확인하고 싶다면 설치한 운영체제에 맞는 한 줄을 사용하세요.

Windows PowerShell:

```powershell
python "$env:USERPROFILE\.codex\skills\naver-blog-assistant\scripts\validate_draft.py" "drafts\글파일.md" --json
```

macOS/Linux:

```bash
python3 ~/.codex/skills/naver-blog-assistant/scripts/validate_draft.py drafts/글파일.md --json
```

검증 결과에는 원고 전문 대신 통과 여부와 글자·문단·소제목 수만 표시됩니다. 직접 실행할 때는 Python 3.10 이상이 필요하며 외부 패키지는 필요하지 않습니다.

기존 Markdown에 YAML 머리말이 없다면 솜솜에게 “이 파일을 원고 템플릿 형식으로 한 번만 변환해줘”라고 요청하면 됩니다.

## 네이버 자동 입력은 두 단계입니다

```text
원고 파일 생성·검증
        ↓
브라우저 도구가 새 편집기에 일괄 입력
        ↓
사용자 검수 또는 명시적 발행
```

Playwright는 브라우저를 클릭하고 입력하는 자동화 도구이며, 그 실행 자체가 모델 토큰을 쓰는 것은 아닙니다. 다만 이 저장소에는 아직 독립 실행형 Playwright 엔진을 묶지 않았습니다. 현재는 설치된 브라우저 제어 도구를 사용하며, 추후 검증된 파일 경로형 실행 엔진을 별도 프로젝트로 연결할 수 있습니다.

## 안전 원칙

- 로그인과 인증은 사용자가 직접 합니다.
- 비밀번호, 인증번호, 쿠키, 세션 파일을 원고나 Git에 넣지 않습니다.
- 기존 게시물과 임시저장 글을 수정하거나 덮어쓰지 않습니다.
- 화면 상태가 예상과 다르면 좌표를 추측하지 않고 중단합니다.
- 기본값은 검수 모드이며, 현재 작업에서 사용자가 명시한 경우에만 발행합니다.

## 저장소 구조

```text
skills/naver-blog-assistant/
├─ SKILL.md
├─ agents/openai.yaml
├─ references/
│  ├─ browser-workflow.md
│  └─ writing-guide.md
├─ scripts/
│  └─ validate_draft.py
├─ tests/
└─ assets/
   ├─ article-request.yaml
   ├─ draft-template.md
   ├─ persona-template.md
   └─ review-checklist.md
```

## 현재 범위

- 글 작성과 로컬 검증: 바로 사용 가능
- 네이버 편집기 입력: 브라우저 제어 기능이 있는 환경에서 사용
- 고정 셀렉터 기반 Playwright 실행 엔진: 연속 성공 검증 후 별도 공개 예정

실제 자동 입력 예시: [GIF](media/somsom-naver-auto-input.gif) · [정지 화면](media/somsom-naver-auto-input-cover.png)

## 라이선스

MIT License로 공개합니다. 개인·팀 프로젝트에서 수정하고 재배포할 수 있습니다.
