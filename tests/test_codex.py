import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexSkillTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex skill ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.skill = self.project / ".agents/skills/youtube-english-study"
        self.run_python(ROOT / "scripts/install_codex.py", "--project", self.project)

    def run_python(self, script, *args, expected=0, env=None):
        result = subprocess.run(
            [sys.executable, "-I", str(script), *map(str, args)],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_install_is_repeatable_and_preserves_edits(self):
        self.assertTrue((self.skill / "assets/template.html").is_file())
        self.assertTrue((self.skill / "references/annotation-guide.md").is_file())
        self.run_python(ROOT / "scripts/install_codex.py", "--project", self.project)
        installed = self.skill / "SKILL.md"
        installed.write_text("local edit", encoding="utf-8")
        self.run_python(ROOT / "scripts/install_codex.py", "--project", self.project, expected=1)
        self.assertEqual(installed.read_text(), "local edit")

    def test_installed_fetch_validate_build(self):
        self.verify_pipeline()

    def test_claude_install_fetch_validate_build(self):
        self.skill = self.project / ".claude/skills/youtube-english-study"
        shutil.copytree(ROOT / "youtube-english-study", self.skill)
        self.verify_pipeline()

    def verify_pipeline(self):
        # A deterministic yt-dlp stand-in exercises fetch's CLI boundary and SRT parser.
        # This verifies the local pipeline, not live YouTube access.
        bin_dir = self.project / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "yt-dlp"
        fake.write_text("#!" + sys.executable + "\n" + '''import json, pathlib, sys
if "-J" in sys.argv:
    print(json.dumps({"id":"fixture0001", "title":"Codex smoke", "duration":12,
                      "subtitles":{"en":[{}]}}))
else:
    target = pathlib.Path(sys.argv[sys.argv.index("-o")+1] + ".en.srt")
    target.write_text("1\\n00:00:00,000 --> 00:00:04,000\\n[Music] Let's head out.\\n\\n"
                      "2\\n00:00:04,000 --> 00:00:08,000\\nBring a hamper.\\n\\n"
                      "3\\n00:00:08,000 --> 00:00:12,000\\nSee you tomorrow.\\n")
''', encoding="utf-8")
        fake.chmod(0o755)
        env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
        scripts = self.skill / "scripts"
        self.run_python(scripts / "fetch.py", "https://youtu.be/fixture0001", self.project, env=env)
        work = self.project / "jingdu-fixture0001"
        sents = json.loads((work / "sents.json").read_text())
        self.assertEqual(len(sents), 3)
        self.assertEqual(sents[0]["en"], "Let's head out.")
        data = {
            "scenes.json": [{"start":1,"title":"准备出门","summary":"练习出门用语。"}],
            "annotations.json": {"annotations":[
                {"i":1,"span":"head out","zh":"出门","type":"phrase"},
                {"i":2,"span":"hamper","zh":"带盖衣物篮","type":"word"}], "corrections":[]},
            "ipa.json": [{"span":"head out","ipa":"/ˌhed ˈaʊt/"},
                         {"span":"hamper","ipa":"/ˈhæmpɚ/"}],
        }
        for name, value in data.items():
            (work / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        self.run_python(scripts / "check.py", work, "--ipa-todo")
        self.assertEqual(len(json.loads((work / "ipa_todo.json").read_text())), 2)
        output = self.project / "output"
        result = self.run_python(scripts / "build.py", work, output)
        self.assertNotIn("NOT PLACED", result.stdout)
        page = (output / "Codex smoke-英语精读本.html").read_text()
        self.assertIn('data-ipa="/ˈhæmpɚ/"', page)
        self.assertIn("出门", page)
        self.assertIn("&amp;t=4s", page)
        self.assertNotRegex(page, r"\{\{[A-Z_]+\}\}")
        if shutil.which("node"):
            js = self.project / "page.js"
            js.write_text("\n".join(re.findall(r"<script[^>]*>(.*?)</script>", page, re.S)))
            check = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
        data["annotations.json"]["annotations"][0]["span"] = "missing expression"
        (work / "annotations.json").write_text(json.dumps(data["annotations.json"]))
        result = self.run_python(scripts / "check.py", work, expected=1)
        self.assertIn("span not found", result.stdout)


if __name__ == "__main__":
    unittest.main()
