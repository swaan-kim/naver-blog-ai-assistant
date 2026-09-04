import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[1]
SKILL_TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


class InstructionBudgetTests(unittest.TestCase):
    def test_skill_and_openai_metadata_have_required_shape(self) -> None:
        self.assertTrue(SKILL_TEXT.startswith("---\n"))
        frontmatter = SKILL_TEXT.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: naver-blog-assistant$")
        self.assertRegex(frontmatter, r"(?m)^description: \S.+$")

        openai_yaml = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        for key in ("display_name:", "short_description:", "default_prompt:"):
            self.assertIn(key, openai_yaml)
        self.assertIn("$naver-blog-assistant", openai_yaml)

    def test_each_runtime_path_stays_under_4000_characters(self) -> None:
        for reference in ("writing-guide.md", "browser-workflow.md"):
            text = (SKILL_DIR / "references" / reference).read_text(encoding="utf-8")
            with self.subTest(reference=reference):
                self.assertLessEqual(len(SKILL_TEXT) + len(text), 4_000)

    def test_local_markdown_links_in_skill_exist(self) -> None:
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", SKILL_TEXT)
        local_links = [link for link in links if "://" not in link and not link.startswith("#")]
        self.assertTrue(local_links)
        for link in local_links:
            with self.subTest(link=link):
                self.assertTrue((SKILL_DIR / link).is_file())

    def test_skill_mentions_only_existing_runtime_resources(self) -> None:
        for relative_path in (
            "assets/draft-template.md",
            "assets/article-request.yaml",
            "assets/persona-template.md",
            "scripts/validate_draft.py",
        ):
            with self.subTest(path=relative_path):
                self.assertIn(relative_path, SKILL_TEXT)
                self.assertTrue((SKILL_DIR / relative_path).is_file())

    def test_readme_local_links_exist(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", readme)
        local_links = [link for link in links if "://" not in link and not link.startswith("#")]
        for link in local_links:
            with self.subTest(link=link):
                self.assertTrue((REPO_ROOT / link).is_file())


if __name__ == "__main__":
    unittest.main()
