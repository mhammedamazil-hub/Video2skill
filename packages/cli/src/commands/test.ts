"use strict";

import * as fs from "fs";
import * as path from "path";
import { execFileSync } from "child_process";
import { enginePaths, engineInstalled } from "../engine";
import { loadConfig, libraryPath } from "../config";

export async function cmdTest(args: string[]): Promise<number> {
  const skillName = args[0];
  if (!skillName) {
    console.error("Usage: video2skill test <skill-name>");
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
    console.log(`Run 'video2skill list' to see available skills.`);
    return 1;
  }

  const { python } = enginePaths();
  const entry = path.join(__dirname, "..", "..", "..", "engine", "bootstrap.py");
  const absEntry = path.resolve(entry);

  console.log(`Video2Skill - test ${skillName}`);
  console.log(`Skill: ${skillDir}`);

  try {
    execFileSync(python, [absEntry, "examine", skillName], {
      stdio: "inherit",
      encoding: "utf8",
      timeout: 900000,
    });
  } catch (err: any) {
    console.error(`Examination failed: ${err?.message ?? String(err)}`);
    return 1;
  }

  console.log("\nExamination complete. Review the evaluation report above.");
  return 0;
}
