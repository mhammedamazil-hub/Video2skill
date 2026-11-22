"use strict";

import * as fs from "fs";
import * as path from "path";
import { loadConfig, libraryPath } from "../config";

export async function cmdList(args: string[]): Promise<number> {
  const json = args.includes("--json");
  const config = loadConfig();
  const lib = libraryPath(config);

  if (!fs.existsSync(lib)) {
    if (json) {
      console.log(JSON.stringify({ skills: [], library: lib }, null, 2));
    } else {
      console.log(`Skill library: ${lib}`);
      console.log("No skills installed yet. Run `video2skill learn <video>` to create one.");
    }
    return 0;
  }

  const entries = fs.readdirSync(lib, { withFileTypes: true }).filter((e) => e.isDirectory());
  const skills = entries.map((e) => {
    const dir = path.join(lib, e.name);
    const manifest = path.join(dir, "skill.json");
    let meta: any = { name: e.name };
    try {
      meta = JSON.parse(fs.readFileSync(manifest, "utf8"));
    } catch {
      // no manifest yet
    }
    return meta;
  });

  if (json) {
    console.log(JSON.stringify({ skills, library: lib, count: skills.length }, null, 2));
    return 0;
  }

  console.log(`Skill library: ${lib}`);
  if (skills.length === 0) {
    console.log("No skills installed yet. Run `video2skill learn <video>` to create one.");
    return 0;
  }
  console.log(`\n${"Name".padEnd(30)} Version  Status`);
  console.log("-".repeat(50));
  for (const s of skills) {
    console.log(`${(s.name ?? "").padEnd(30)} ${(s.version ?? "0.1.0").padEnd(8)} ${s.status ?? "draft"}`);
  }
  console.log(`\nTotal: ${skills.length}`);
  return 0;
}
