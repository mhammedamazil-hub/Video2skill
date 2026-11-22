"use strict";

import * as fs from "fs";
import * as path from "path";
import { loadConfig, libraryPath } from "../config";

export async function cmdInspect(args: string[]): Promise<number> {
  const skillName = args[0];
  if (!skillName) {
    console.error("Usage: video2skill inspect <skill-name>");
    return 1;
  }

  const config = loadConfig();
  const lib = libraryPath(config);
  const skillDir = path.join(lib, skillName);
  if (!fs.existsSync(skillDir)) {
    console.error(`Skill not found in library: ${skillName}`);
    return 1;
  }

  console.log(`Skill: ${skillName}`);
  console.log(`Path: ${skillDir}`);

  const manifest = path.join(skillDir, "skill.json");
  if (fs.existsSync(manifest)) {
    const meta = JSON.parse(fs.readFileSync(manifest, "utf8"));
    console.log("\nMetadata:");
    console.log(JSON.stringify(meta, null, 2));
  }

  const skillMd = path.join(skillDir, "SKILL.md");
  if (fs.existsSync(skillMd)) {
    console.log("\nSKILL.md (first 80 lines):");
    const lines = fs.readFileSync(skillMd, "utf8").split("\n");
    console.log(lines.slice(0, 80).join("\n"));
    if (lines.length > 80) console.log(`\n... (${lines.length - 80} more lines)`);
  }

  const evidenceDir = path.join(skillDir, "evidence");
  if (fs.existsSync(evidenceDir)) {
    const files = fs.readdirSync(evidenceDir);
    console.log(`\nEvidence files: ${files.length}`);
    for (const f of files.slice(0, 10)) {
      console.log(`  - ${f}`);
    }
  }

  return 0;
}
