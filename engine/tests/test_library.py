"""Tests for the versioned skill library store."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library.store import SkillLibrary, SkillManifest
from agents.architect import SkillArchitect


def test_library_round_trip(tmp_path):
    lib = SkillLibrary(str(tmp_path / "lib"))
    m = SkillManifest(
        id="skill-test",
        name="skill-test",
        description="A test skill.",
        source="https://example.com/video",
        providers=["anthropic"],
        models=["claude-3-5-sonnet-20241022"],
    )
    lib.save(m)
    loaded = lib.get("skill-test")
    assert loaded is not None
    assert loaded.name == "skill-test"
    assert loaded.status == "draft"
    assert loaded.version == "0.1.0"

    skills = lib.list_skills()
    assert any(s["name"] == "skill-test" for s in skills)


def test_archive_version_preserves_prior():
    tmp = Path(tempfile.mkdtemp())
    lib = SkillLibrary(str(tmp / "lib"))
    m = SkillManifest(id="skill-v", name="skill-v", description="v", version="0.1.0")
    lib.save(m)
    (lib._skill_dir("skill-v") / "SKILL.md").write_text("# skill v1", encoding="utf-8")

    lib.archive_version("skill-v")
    versions = list((lib._skill_dir("skill-v") / "versions").iterdir())
    assert len(versions) == 1
    assert (versions[0] / "SKILL.md").read_text(encoding="utf-8") == "# skill v1"


def test_skill_md_write_read():
    tmp = Path(tempfile.mkdtemp())
    lib = SkillLibrary(str(tmp / "lib"))
    lib.write_skill_md("skill-x", "---\nname: skill-x\n---\n\n# body")
    assert lib.read_skill_md("skill-x") == "---\nname: skill-x\n---\n\n# body"


def test_architect_slug():
    arch = SkillArchitect()
    assert arch._slug("Create a 3D Cube!") == "create-a-3d-cube"
    assert arch._slug("!!!") == "skill"


if __name__ == "__main__":
    import tempfile

    test_library_round_trip(Path(tempfile.mkdtemp()))
    test_archive_version_preserves_prior()
    test_skill_md_write_read()
    test_architect_slug()
    print("test_library.py: OK")
