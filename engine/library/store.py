# Versioned local skill library.

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SkillManifest:
    id: str
    name: str
    description: str
    version: str = "0.1.0"
    status: str = "draft"  # draft | verified | failed | archived
    capability: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    sas: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    evaluation_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SkillLibrary:
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _skill_dir(self, skill_id: str) -> Path:
        return self.root / skill_id

    def list_skills(self) -> list[dict[str, Any]]:
        skills = []
        if not self.root.exists():
            return skills
        for entry in sorted(self.root.iterdir()):
            if entry.is_dir():
                manifest_path = entry / "skill.json"
                if manifest_path.exists():
                    try:
                        skills.append(json.loads(manifest_path.read_text(encoding="utf-8")))
                    except (json.JSONDecodeError, OSError):
                        skills.append({"name": entry.name, "status": "unknown", "version": "?"})
                else:
                    skills.append({"name": entry.name, "status": "unmanifested", "version": "?"})
        return skills

    def get(self, skill_id: str) -> SkillManifest | None:
        manifest_path = self._skill_dir(skill_id) / "skill.json"
        if not manifest_path.exists():
            return None
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        return SkillManifest(**raw)

    def save(self, manifest: SkillManifest) -> None:
        skill_dir = self._skill_dir(manifest.id)
        skill_dir.mkdir(parents=True, exist_ok=True)
        manifest.updated_at = datetime.now(timezone.utc).isoformat()
        (skill_dir / "skill.json").write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    def save_sas(self, source: str, sas: dict[str, Any]) -> None:
        skill_id = "sas_" + uuid.uuid5(uuid.NAMESPACE_URL, source).hex[:12]
        self._skill_dir(skill_id).mkdir(parents=True, exist_ok=True)
        (self._skill_dir(skill_id) / "sas.json").write_text(json.dumps(sas, indent=2), encoding="utf-8")

    def archive_version(self, skill_id: str) -> None:
        skill_dir = self._skill_dir(skill_id)
        versions_dir = skill_dir / "versions"
        versions_dir.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = versions_dir / stamp
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for item in skill_dir.iterdir():
            if item.name == "versions":
                continue
            if item.is_dir():
                shutil.copytree(item, dest / item.name)
            else:
                shutil.copy2(item, dest / item.name)

    def write_skill_md(self, skill_id: str, content: str) -> None:
        skill_dir = self._skill_dir(skill_id)
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

    def read_skill_md(self, skill_id: str) -> str | None:
        p = self._skill_dir(skill_id) / "SKILL.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None
