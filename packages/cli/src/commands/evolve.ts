"use strict";

import * as fs from "fs";
import * as path from "path";
import { execFileSync } from "child_process";
import { enginePaths, engineInstalled } from "../engine";
import { loadConfig, libraryPath } from "../config";

export async function cmdEvolve(args: string[]): Promise<number> {
  const skillName = args[0];
  if (!skillName) {
    console.error("Usage: video2skill evolve <skill-name>");
    return 1;
  }

  const config = loadConfig();
  if (!engineInstalled()) {
    console.error("Python engine not initialized. Run `video2skill init` first.");
    return 1;
  }

  const lib = libraryPath(config);
  const skillDir = path.join(lib, skillName);
  if (!fs.existsSync(skillDir)) {
    console.error(`Skill not found in library: ${skillName}`);
    return 1;
  }

  const { python } = enginePaths();
  const entry = path.join(__dirname, "..", "..", "..", "engine", "bootstrap.py");
  const absEntry = path.resolve(entry);

  console.log(`Video2Skill - evolve ${skillName}`);

  try {
    execFileSync(python, [absEntry, "evolve", skillName], {
      stdio: "inherit",
      encoding: "utf8",
      timeout: 900000,
    });
  } catch (err: any) {
    console.error(`Evolution failed: ${err?.message ?? String(err)}`);
    return 1;
  }

  console.log("\nEvolution complete. Re-run `video2skill test <skill-name>` to verify the improved skill.");
  return 0;
}
