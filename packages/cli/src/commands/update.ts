"use strict";

import { enginePaths, engineInstalled } from "../engine";
import { execFileSync } from "child_process";

export async function cmdUpdate(args: string[]): Promise<number> {
  if (!engineInstalled()) {
    console.error("Python engine not initialized. Run `video2skill init` first.");
    return 1;
  }

  const { python } = enginePaths();
  const pip = pathDirname(python) + "/pip";

  console.log("Video2Skill - updating engine components");
  try {
    execFileSync(pip, ["install", "--upgrade", "pip", "pyyaml", "requests"], {
      stdio: "inherit",
      encoding: "utf8",
      timeout: 600000,
    });
  } catch (err: any) {
    console.error(`Update failed: ${err?.message ?? String(err)}`);
    return 1;
  }

  console.log("\nEngine components updated.");
  return 0;
}

function pathDirname(p: string): string {
  const i = p.lastIndexOf("/");
  return i >= 0 ? p.slice(0, i) : ".";
}
